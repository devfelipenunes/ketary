//! Isolated CPython research extension. No raw-pointer interface in our code.
use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyRuntimeError};
use pyo3::types::{PyBytes,PyInt,PyAny};
use std::collections::BTreeMap;
mod core;
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
}
#[pymodule]
fn ketary_native_research(m:&Bound<'_,PyModule>)->PyResult<()>{
 m.add_class::<PackedCircuit>()?;
 m.add("BudgetExceeded",m.py().get_type::<BudgetExceeded>())?;
 m.add("SCHEMA_VERSION",1)?;
 Ok(())
}
