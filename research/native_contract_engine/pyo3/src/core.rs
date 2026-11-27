use std::collections::HashMap;
type Key=(u64,u64);
type Co=(i128,i128);
pub(crate) type Term=(Key,Co);
pub(crate) fn cliff(op:u8,a:u32,b:u32,mut x:u64,mut z:u64)->(u64,u64,bool){
 let aa=1u64<<a;let xa=x&aa!=0;let za=z&aa!=0;
 let r=match op {
  0=>{if xa!=za{x^=aa;z^=aa;}xa&&za},
  1=>{if xa{z^=aa;}xa&&!za},
  2=>{if xa{z^=aa;}xa&&za},
  3=>za,4=>xa,
  5=>{let bb=1u64<<b;let xb=x&bb!=0;let zb=z&bb!=0;
   if xa{x^=bb;}if zb{z^=aa;}xa&&zb&&!(xb^za)},
  _=>unreachable!()
 };(x,z,r)
}
fn add(v:&mut Vec<Option<Term>>,m:&mut HashMap<Key,usize>,k:Key,c:Co,cap:usize)->Result<(),i32>{
 if let Some(&i)=m.get(&k){
  let (_,old)=v[i].unwrap();let s=(old.0+c.0,old.1+c.1);
  if s==(0,0){m.remove(&k);v[i]=None;}else{v[i]=Some((k,s));}
 }else if c!=(0,0){m.insert(k,v.len());v.push(Some((k,c)));}
 if m.len()>cap{Err(4)}else{Ok(())}
}
pub(crate) fn run(g:&[u8],n:u32,x:u64,z:u64,r:u8,cap:usize,max_work:u64)->Result<(Vec<Term>,u64,u64,u64),i32>{
 if g.len()>300_000||g.len()%3!=0||n==0||n>64||r>1||(n<64&&(x|z)>>n!=0)||cap==0||cap>4096||max_work==0||max_work>2_000_000{return Err(1)}
 let mut tc=0u64;
 for v in g.chunks_exact(3){let(op,a,b)=(v[0],v[1] as u32,v[2] as u32);
  if op>7||a>=n||(op==5&&(b>=n||a==b))||(op!=5&&b!=0){return Err(1)}
  if op>=6{tc+=1;}
 }
 if tc>32{return Err(2)}
 let mut terms=vec![((x,z),(if r==0{1}else{-1},0))];let mut work=0;let mut peak=1;
 for v in g.chunks_exact(3).rev(){
  work+=terms.len() as u64;if work>max_work{return Err(3)}
  let(op,a,b)=(v[0],v[1] as u32,v[2] as u32);
  if op<6 {
   for ((x,z),(u,w)) in terms.iter_mut(){let(xx,zz,s)=cliff(op,a,b,*x,*z);*x=xx;*z=zz;if s{*u=-*u;*w=-*w;}}
  }else{
   let aa=1u64<<a;let mut out=Vec::with_capacity(2*terms.len());let mut m=HashMap::with_capacity(2*terms.len());
   for ((x,z),(u,w)) in terms{
    if x&aa==0{add(&mut out,&mut m,(x,z),(2*u,2*w),cap)?;}
    else{
     add(&mut out,&mut m,(x,z),(2*w,u),cap)?;
     let s=if (z&aa!=0)==(op==6){1}else{-1};
     add(&mut out,&mut m,(x,z^aa),(s*2*w,s*u),cap)?;
    }
   }
   terms=out.into_iter().flatten().collect();
  }
  peak=peak.max(terms.len() as u64);
 }
 terms.sort_unstable_by_key(|t|t.0);Ok((terms,tc,peak,work))
}
