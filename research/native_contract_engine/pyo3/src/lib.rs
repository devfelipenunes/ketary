//! Isolated CPython research extension. No raw-pointer interface in our code.
use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyRuntimeError};
use pyo3::types::{PyBytes,PyInt,PyAny};
use std::collections::BTreeMap;
mod core;
mod monomial;
mod tableau22;
type Signed=(u64,u64,u8);
type Witness=(String,Vec<i8>,(i128,i128),u64);
type Prop=(Vec<(u64,u64,i128,i128)>,u64,u64,u64);
type Verdict=(bool,Option<Witness>,u64,u64);
pyo3::create_exception!(ketary_native_research, BudgetExceeded, PyRuntimeError);
fn err(code:i32)->PyErr {
 match code {
 2=>BudgetExceeded::new_err("T-count cap"),
 3=>BudgetExceeded::new_err("term-work cap"),
 4=>BudgetExceeded::new_err("live term cap"),
 _=>PyValueError::new_err("native admission")
 }
}
fn exact_u64(v:&Bound<'_,PyAny>)->PyResult<u64>{
 if !v.is_exact_instance_of::<PyInt>(){return Err(PyValueError::new_err("expected exact int"))}
 v.extract()
}
fn valid(n:u32,p:Signed)->bool {p.2<=1&&(n==64||(p.0|p.1)>>n==0)}
fn add(m:&mut BTreeMap<u64,(i128,i128)>,key:u64,c:(i128,i128)){
 let o=m.get(&key).copied().unwrap_or((0,0));let s=(o.0+c.0,o.1+c.1);
 if s==(0,0){m.remove(&key);}else{m.insert(key,s);}
}
fn witness(n:u32,terms:&[core::Term],k:u64,pre:Signed)->Option<Witness>{
 // Match Python difference insertion order: sorted terms, pre appended
 // if absent, otherwise replaced in place or removed.
 let target=(pre.0,pre.1);let sub=if pre.2==0{-(1i128<<k)}else{1i128<<k};
 let mut diff=Vec::with_capacity(terms.len()+1);let mut found=false;
 for &(key,(a,b)) in terms {
  let co=if key==target{found=true;(a+sub,b)}else{(a,b)};
  if co!=(0,0){diff.push((key,co));}
 }
 if !found{diff.push((target,(sub,0)));}
 let &((x,z),_)=diff.first()?;
 let mut axes=String::with_capacity(n as usize);let mut ax=0u64;let mut az=0u64;
 for i in 0..n {
  let bit=1u64<<i;let a=x&bit!=0;let b=z&bit!=0;
  let c=match(a,b){(true,true)=>'Y',(true,false)=>'X',_=>'Z'};
  axes.push(c);if c!='Z'{ax|=bit;}if c!='X'{az|=bit;}
 }
 let mut poly=BTreeMap::new();
 for ((x,z),co) in diff {
  let mask=x|z;if ((x^ax)|(z^az))&mask==0{add(&mut poly,mask,co);}
 }
 debug_assert!(!poly.is_empty());
 let mut signs=Vec::with_capacity(n as usize);
 for i in 0..n {
  if poly.len()==1&&poly.contains_key(&0){signs.resize(n as usize,1);break;}
  let bit=1u64<<i;let mut plus=BTreeMap::new();
  for (&mask,&co) in &poly{add(&mut plus,mask&!bit,co);}
  if !plus.is_empty(){signs.push(1);poly=plus;}
  else{
   let mut minus=BTreeMap::new();
   for (&mask,&(a,b)) in &poly{
    let c=if mask&bit!=0{(-a,-b)}else{(a,b)};add(&mut minus,mask&!bit,c);
   }
   debug_assert!(!minus.is_empty());signs.push(-1);poly=minus;
  }
 }
 Some((axes,signs,*poly.get(&0).expect("nonzero polynomial"),k))
}
// Exact cancellation and backward support cone. Charge three gate scans
// conservatively; the existing term-work cap does not count witness cost.
fn cone(g:&[u8],post:Signed)->Vec<u8>{
 let inv=[0u8,2,1,3,4,5,7,6];let mut stack:Vec<[u8;3]>=Vec::with_capacity(g.len()/3);
 for v in g.chunks_exact(3){
  let row=[v[0],v[1],v[2]];
  if stack.last()==Some(&[inv[row[0] as usize],row[1],row[2]]){stack.pop();}else{stack.push(row);}
 }
 let mut support=post.0|post.1;let mut kept=Vec::new();
 for row in stack.into_iter().rev(){
  let wires=(1u64<<row[1])|if row[0]==5{1u64<<row[2]}else{0};
  if support&wires!=0{support|=wires;kept.push(row);}
 }
 kept.into_iter().rev().flatten().collect()
}
// Clifford bit slicing: each lane is one independent signed Pauli.
// The caller admits only a prefix affordable under the old scalar budget.
fn bitslice(g:&[u8],n:u32,ps:&[Signed])->Vec<Signed>{
 let mut x=[0u64;64];let mut z=[0u64;64];let mut r=0u64;
 for (j,&(a,b,s)) in ps.iter().enumerate(){
  let lane=1u64<<j;
  if s!=0{r|=lane;}
  for i in 0..n as usize{if (a>>i)&1!=0{x[i]|=lane;}if (b>>i)&1!=0{z[i]|=lane;}}
 }
 for v in g.chunks_exact(3).rev(){
  let a=v[1] as usize;let b=v[2] as usize;let xa=x[a];let za=z[a];
  match v[0]{
   0=>{r^=xa&za;x[a]=za;z[a]=xa;},
   1=>{r^=xa&!za;z[a]^=xa;},
   2=>{r^=xa&za;z[a]^=xa;},
   3=>r^=za,4=>r^=xa,
   5=>{let xb=x[b];let zb=z[b];r^=xa&zb&!(xb^za);x[b]^=xa;z[a]^=zb;},
   _=>unreachable!("Clifford-only path")
  }
 }
 ps.iter().enumerate().map(|(j,_)|{
  let mut a=0u64;let mut b=0u64;
  for i in 0..n as usize{a|=((x[i]>>j)&1)<<i;b|=((z[i]>>j)&1)<<i;}
  (a,b,((r>>j)&1) as u8)
 }).collect()
}
#[pyclass(frozen)]
struct PackedCircuit{width:u32,gates:Vec<u8>}
#[pymethods]
impl PackedCircuit {
 #[new]
 fn new(width:&Bound<'_,PyAny>,gates:&Bound<'_,PyBytes>)->PyResult<Self>{
  let n=exact_u64(width)?;
  let g=gates.as_bytes();
  if !(1..=64).contains(&n)||g.len()>300_000||g.len()%3!=0{return Err(err(1))}
  let n=n as u32;
  for v in g.chunks_exact(3){
   let(op,a,b)=(v[0],v[1] as u32,v[2] as u32);
   if op>7||a>=n||(op==5&&(b>=n||a==b))||(op!=5&&b!=0){return Err(err(1))}
  }
  Ok(Self{width:n,gates:g.to_vec()})
 }
 #[getter]
 fn width(&self)->u32{self.width}
 #[getter]
 fn gate_count(&self)->usize{self.gates.len()/3}
 fn propagate(&self,py:Python<'_>,post:Signed,max_terms:usize,max_work:u64)->PyResult<Prop>{
  if !valid(self.width,post){return Err(err(1))}
  let (terms,k,peak,work)=py.detach(||core::run(&self.gates,self.width,post.0,post.1,post.2,max_terms,max_work)).map_err(err)?;
  Ok((terms.into_iter().map(|((x,z),(a,b))|(x,z,a,b)).collect(),k,peak,work))
 }
 fn transition(&self,py:Python<'_>,pre:Signed,post:Signed,max_terms:usize,max_work:u64)->PyResult<Verdict>{
  if !valid(self.width,pre)||!valid(self.width,post){return Err(err(1))}
  py.detach(||{
   let (terms,k,peak,work)=core::run(&self.gates,self.width,post.0,post.1,post.2,max_terms,max_work)?;
   let w=witness(self.width,&terms,k,pre);
   Ok((w.is_none(),w,peak,work))
  }).map_err(err)
 }
 // One native call with shared conservative term-work budget.
 fn transition_batch(&self,py:Python<'_>,items:&Bound<'_,pyo3::types::PyTuple>,max_terms:usize,max_work:u64,adaptive:bool)->PyResult<Vec<Option<Verdict>>>{
  if items.len()==0||items.len()>64||max_terms==0||max_terms>4096||max_work==0||max_work>2_000_000{return Err(err(1))}
  let obs:Vec<(Signed,Signed)>=items.extract()?;
  if obs.iter().any(|(a,b)|!valid(self.width,*a)||!valid(self.width,*b)){return Err(err(1))}
  py.detach(||{
   // Keep old sequential abort semantics, including the exact budget boundary.
   let count=(self.gates.len()/3) as u64;
   if !adaptive&&obs.len()>=8&&self.gates.chunks_exact(3).all(|v|v[0]<6){
    let m=if count==0{obs.len()}else{obs.len().min((max_work/count) as usize)};
    let posts:Vec<Signed>=obs[..m].iter().map(|(_,p)|*p).collect();
    let images=bitslice(&self.gates,self.width,&posts);
    let mut out=Vec::with_capacity(obs.len());
    for ((pre,_),(x,z,r)) in obs[..m].iter().zip(images){
     let terms=[((x,z),(if r==0{1}else{-1},0))];
     let w=witness(self.width,&terms,0,*pre);out.push(Some((w.is_none(),w,1,count)));
    }
    out.resize(obs.len(),None);return Ok(out);
   }
   let mut remaining=max_work;let mut out=Vec::with_capacity(obs.len());
   for (pre,post) in obs{
    if remaining==0{out.push(None);continue;}
    let reduced;
    let gates=if adaptive{
     let cost=3*(self.gates.len()/3) as u64;
     if cost>=remaining{remaining=0;out.push(None);continue;}
     remaining-=cost;reduced=cone(&self.gates,post);reduced.as_slice()
    }else{self.gates.as_slice()};
    match core::run(gates,self.width,post.0,post.1,post.2,max_terms,remaining){
     Ok((terms,k,peak,work))=>{remaining-=work;let w=witness(self.width,&terms,k,pre);out.push(Some((w.is_none(),w,peak,work)));}
     Err(2|3|4)=>{remaining=0;out.push(None);}
     Err(e)=>return Err(err(e)),
    }
   }
   Ok(out)
  })
 }
 // First failing projected generator, or budget-inconclusive. The
 // compression and witness stay native; only a single witness crosses FFI.
 fn projected(&self,py:Python<'_>,items:&Bound<'_,pyo3::types::PyTuple>,mask:u64,max_terms:usize,max_work:u64,adaptive:bool)->PyResult<(u8,usize,Option<Witness>,u64)>{
  if items.len()==0||items.len()>128||mask==0||(self.width<64&&mask>>self.width!=0)||max_terms==0||max_terms>4096||max_work==0||max_work>2_000_000{return Err(err(1))}
  let obs:Vec<(Signed,Signed)>=items.extract()?;
  if obs.iter().any(|(a,b)|!valid(self.width,*a)||!valid(self.width,*b)||a.0&mask!=0){return Err(err(1))}
  py.detach(||{
   let mut remaining=max_work;
   for (i,(pre,post)) in obs.iter().copied().enumerate(){
    if remaining==0{return Ok((2,i,None,max_work));}
    let reduced;
    let gates=if adaptive{
     let cost=3*(self.gates.len()/3) as u64;
     if cost>=remaining{return Ok((2,i,None,max_work));}
     remaining-=cost;reduced=cone(&self.gates,post);reduced.as_slice()
    }else{self.gates.as_slice()};
    match core::run(gates,self.width,post.0,post.1,post.2,max_terms,remaining){
     Ok((terms,k,_,work))=>{
      remaining-=work;
      let mut compressed:BTreeMap<(u64,u64),(i128,i128)>=BTreeMap::new();
      for ((x,z),(a,b)) in terms{
       if x&mask==0{
        let key=(x,z&!mask);
        let old=compressed.get(&key).copied().unwrap_or((0,0));
        let co=(old.0+a,old.1+b);
        if co==(0,0){compressed.remove(&key);}else{compressed.insert(key,co);}
       }
      }
      let terms:Vec<core::Term>=compressed.into_iter().collect();
      let w=witness(self.width,&terms,k,(pre.0,pre.1&!mask,pre.2));
      if w.is_some(){return Ok((1,i,w,max_work-remaining));}
     }
     Err(2|3|4)=>return Ok((2,i,None,max_work)),
     Err(e)=>return Err(err(e)),
    }
   }
   Ok((0,obs.len(),None,max_work-remaining))
  })
 }
 fn monomial_action(&self,py:Python<'_>,other:PyRef<'_,PackedCircuit>,mask:u64,max_work:u64)->PyResult<monomial::Outcome>{
  if self.width!=other.width||mask==0||(self.width<64&&mask>>self.width!=0)||self.gates.len()+other.gates.len()>300_000||max_work==0||max_work>2_000_000{return Err(err(1))}
  let b:&PackedCircuit=&other;
  Ok(py.detach(||monomial::verify(&self.gates,&b.gates,self.width,mask,max_work)))
 }
}
// Private experimental class; no changes to existing PackedCircuit semantics.
#[pyclass(frozen)]
struct CliffordTableau { table:tableau22::Tableau }
#[pymethods]
impl CliffordTableau {
 #[new]
 fn new(py:Python<'_>,circuit:PyRef<'_,PackedCircuit>,max_build_work:&Bound<'_,PyAny>)->PyResult<Self>{
  let cap=exact_u64(max_build_work)?;
  if cap==0||cap>2_000_000||circuit.gates.chunks_exact(3).any(|g|g[0]>=6){return Err(err(1))}
  let n=circuit.width;let g=&circuit.gates;
  // Logical bit-slice construction bound; not an allocator or time guarantee.
  let cost=2*(g.len()/3) as u64+4*(n as u64)*(n as u64);
  if cost>cap{return Err(err(3))}
  let table=py.detach(||tableau22::Tableau::build(n,g));
  Ok(Self{table})
 }
 #[getter]
 fn width(&self)->u32{self.table.width()}
 fn image(&self,post:Signed)->PyResult<Signed>{
  if !valid(self.table.width(),post){return Err(err(1))}
  Ok(self.table.image(post))
 }
 fn images(&self,py:Python<'_>,items:&Bound<'_,pyo3::types::PyTuple>,workers:&Bound<'_,PyAny>,max_work:&Bound<'_,PyAny>)->PyResult<Vec<Signed>>{
  let workers=exact_u64(workers)?;let cap=exact_u64(max_work)?;
  if items.is_empty()||items.len()>4096||!(1..=8).contains(&workers)||cap==0||cap>2_000_000{return Err(err(1))}
  let ps:Vec<Signed>=items.extract()?;
  if ps.iter().any(|&p|!valid(self.table.width(),p)){return Err(err(1))}
  let cost: u64=ps.iter().map(|p|1+p.0.count_ones() as u64+p.1.count_ones() as u64).sum();
  if cost>cap{return Err(err(3))}
  Ok(py.detach(||self.table.batch(&ps,workers as usize)))
 }
}
#[pymodule]
fn ketary_native_research(m:&Bound<'_,PyModule>)->PyResult<()>{
 m.add_class::<PackedCircuit>()?;
 m.add_class::<CliffordTableau>()?;
 m.add("BudgetExceeded",m.py().get_type::<BudgetExceeded>())?;
 m.add("SCHEMA_VERSION",1)?;
 Ok(())
}
