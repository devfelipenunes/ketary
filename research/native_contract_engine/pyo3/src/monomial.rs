//! Exact monomial action on clean inputs; fixed, independently tested CCX pattern.
//! Component partition of the UNION of both circuits. No statevector allocation.
type Op=(u8,u8,u8,u8);
pub(crate) type Evidence=(u64,u64,u64,u64,u64,u8,u8);
pub(crate) type Outcome=(u8,String,Option<Evidence>,u64);
fn decode(g:&[u8])->Option<Vec<Op>>{
 let mut out=Vec::new();let mut i=0;
 while i<g.len(){
  let v=&g[i..i+3];
  if v[0]==0{
   if i+45>g.len(){return None;}
   let t=v[1];let b=g[i+4];let a=g[i+10];
   if a==b||a==t||b==t{return None;}
   let expected=[[0,t,0],[5,b,t],[7,t,0],[5,a,t],[6,t,0],[5,b,t],[7,t,0],[5,a,t],[6,b,0],[6,t,0],[0,t,0],[5,a,b],[6,a,0],[7,b,0],[5,a,b]];
   if !g[i..i+45].chunks_exact(3).zip(expected.iter()).all(|(x,y)|x==y.as_slice()){return None;}
   out.push((8,a,b,t));i+=45;
  }else{out.push((v[0],v[1],v[2],0));i+=3;}
 }
 Some(out)
}
fn wires(o:Op)->u64{
 let (k,a,b,c)=o;(1u64<<a)|if k==8{(1u64<<b)|(1u64<<c)}else if k==5{1u64<<b}else{0}
}
fn image(ops:&[Op],mut x:u64)->(u64,u8){
 let mut p=0u8;
 for &(k,a,b,c) in ops{
  let bit=(x>>a)&1;
  match k{
   1=>p=(p+2*bit as u8)%8,2=>p=(p+6*bit as u8)%8,
   3=>x^=1u64<<a,4=>p=(p+4*bit as u8)%8,
   5=>x^=bit<<b,6=>p=(p+bit as u8)%8,7=>p=(p+7*bit as u8)%8,
   8=>x^=(bit&((x>>b)&1))<<c,_=>unreachable!()
  }
 }
 (x,p)
}
pub(crate) fn verify(a:&[u8],b:&[u8],n:u32,clean:u64,budget:u64)->Outcome{
 // Conservative charge for decode/partition/grouping plus evaluations.
 let scans=4*((a.len()+b.len())/3) as u64+u64::from(n)*64;
 if scans>budget{return (2,"preprocessing budget".into(),None,budget);}
 let (aa,bb)=match(decode(a),decode(b)){(Some(a),Some(b))=>(a,b),_=>(return (3,"non-monomial gate pattern".into(),None,scans))};
 let mut groups:Vec<u64>=(0..n).map(|i|1u64<<i).collect();
 for op in aa.iter().chain(bb.iter()){
  let w=wires(*op);let mut m=w;
  groups.retain(|g|{if *g&w!=0{m|=*g;false}else{true}});
  groups.push(m);
 }
 groups.sort_unstable();
 let mut work=scans;
 for m in groups{
  let data:Vec<u32>=(0..n).filter(|i|m&(1u64<<i)!=0&&clean&(1u64<<i)==0).collect();
  if data.len()>12{return (2,"component data cap".into(),None,work);}
  let ga:Vec<Op>=aa.iter().copied().filter(|o|wires(*o)&m!=0).collect();
  let gb:Vec<Op>=bb.iter().copied().filter(|o|wires(*o)&m!=0).collect();
  let per=(ga.len()+gb.len()+data.len()+1) as u64;
  let mut initial=0;
  for k in 0..(1u64<<data.len()){
   if per>budget-work{return (2,"basis evaluation budget".into(),None,budget);}
   work+=per;
   let x=data.iter().enumerate().fold(0u64,|s,(i,w)|s|(((k>>i)&1)<<w));
   let (y,p)=image(&ga,x);let (z,q)=image(&gb,x);let delta=(p+8-q)%8;
   if y!=z{return (1,"basis output differs".into(),Some((m,x,x,y,z,delta,delta)),work);}
   if k==0{initial=delta;}else if initial!=delta{return (1,"relative phase differs".into(),Some((m,0,x,y,z,initial,delta)),work);}
  }
 }
 (0,"all component permutations and relative phases agree".into(),None,work)
}
