//! Persistent inverse Clifford tableau, independent of gate count at query.
//! Images are X^x Z^z times i^phase. All shifts are bounded by admission.
use super::{Signed,bitslice};
#[derive(Clone,Copy)]
struct Row {x:u64,z:u64,k:u8}
impl Row {
 fn from_signed(p:Signed)->Self {
  Self{x:p.0,z:p.1,k:(((p.0&p.1).count_ones()+2*p.2 as u32)&3) as u8}
 }
 fn mul(self,b:Self)->Self {
  Self{x:self.x^b.x,z:self.z^b.z,k:(self.k+b.k+2*((self.z&b.x).count_ones()&1) as u8)&3}
 }
}
pub(crate) struct Tableau {n:u32,x:Vec<Row>,z:Vec<Row>}
impl Tableau {
 pub(crate) fn build(n:u32,g:&[u8])->Self {
  let xs:Vec<Signed>=(0..n).map(|i|(1u64<<i,0,0)).collect();
  let zs:Vec<Signed>=(0..n).map(|i|(0,1u64<<i,0)).collect();
  Self{n,x:bitslice(g,n,&xs).into_iter().map(Row::from_signed).collect(),z:bitslice(g,n,&zs).into_iter().map(Row::from_signed).collect()}
 }
 pub(crate) fn width(&self)->u32 {self.n}
 // Exact size/capacity payload accounting for this object only; not RSS
 // or allocator metadata, temporary construction or Python overhead.
 pub(crate) fn storage_bytes(&self)->(usize,usize){
  (std::mem::size_of::<Self>(),(self.x.capacity()+self.z.capacity())*std::mem::size_of::<Row>())
 }
 pub(crate) fn image(&self,p:Signed)->Signed {
  let mut r=Row{x:0,z:0,k:(((p.0&p.1).count_ones()+2*p.2 as u32)&3) as u8};
  let (mut x,mut z)=(p.0,p.1);
  while x!=0 {let i=x.trailing_zeros() as usize;r=r.mul(self.x[i]);x&=x-1;}
  while z!=0 {let i=z.trailing_zeros() as usize;r=r.mul(self.z[i]);z&=z-1;}
  let k=(r.k+4-((r.x&r.z).count_ones()&3) as u8)&3;
  debug_assert!(k==0||k==2);
  (r.x,r.z,k>>1)
 }
 pub(crate) fn batch(&self,ps:&[Signed],workers:usize)->Vec<Signed> {
  if workers==1||ps.len()<128 {return ps.iter().map(|&p|self.image(p)).collect();}
  let chunk=ps.len().div_ceil(workers);
  // Scoped native threads, deterministic output order; no Python callbacks.
  std::thread::scope(|scope|{
   let handles:Vec<_>=ps.chunks(chunk).map(|part|scope.spawn(move||part.iter().map(|&p|self.image(p)).collect::<Vec<_>>())).collect();
   handles.into_iter().flat_map(|h|h.join().expect("admitted tableau computation")).collect()
  })
 }
}


// Opt-in Four Russians-style 4-bit lookup, with the same ordered Pauli
// multiplication as the baseline. At most 32*16 rows for 64 qubits.
pub(crate) struct Lookup {n:u32,groups:Vec<[Row;16]>}
impl Lookup {
 pub(crate) fn build(t:&Tableau)->Self{
  let mut groups=Vec::new();
  let id=Row{x:0,z:0,k:0};
  for rows in [&t.x,&t.z]{
   for part in rows.chunks(4){
    let mut g=[id;16];
    for (mask,out) in g.iter_mut().enumerate().skip(1){
     let mut r=id;
     for (i,&row) in part.iter().enumerate(){if mask&(1<<i)!=0{r=r.mul(row);}}
     *out=r;
    }
    groups.push(g);
   }
  }
  Self{n:t.n,groups}
 }
 pub(crate) fn storage_bytes(&self)->usize{self.groups.capacity()*std::mem::size_of::<[Row;16]>()}
 pub(crate) fn width(&self)->u32{self.n}
 pub(crate) fn image(&self,p:Signed)->Signed{
  let mut r=Row{x:0,z:0,k:(((p.0&p.1).count_ones()+2*p.2 as u32)&3) as u8};
  let chunks=self.n.div_ceil(4) as usize;
  for (offset,mut mask) in [(0,p.0),(chunks,p.1)]{
   while mask!=0{
    let i=mask.trailing_zeros() as usize/4;
    let v=((mask>>(4*i))&15) as usize;
    r=r.mul(self.groups[offset+i][v]);mask&=!(15u64<<(4*i));
   }
  }
  let k=(r.k+4-((r.x&r.z).count_ones()&3) as u8)&3;
  debug_assert!(k==0||k==2);
  (r.x,r.z,k>>1)
 }
}
