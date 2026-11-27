//! Explicit 128-lane SSE2 Clifford bit slicing, experimental and opt-in.
//! x86_64 guarantees SSE2; portable fallback is two existing scalar slices.
//! No raw memory loads/stores; all registers are constructed from valid u64s.
use super::{Signed,bitslice};
pub(crate) fn images(g:&[u8],n:u32,ps:&[Signed])->Vec<Signed>{
 #[cfg(target_arch="x86_64")]
 { // SAFETY: SSE2 is baseline on x86_64, inputs admitted by PackedCircuit.
  unsafe { return x86(g,n,ps); }
 }
 #[cfg(not(target_arch="x86_64"))]
 { ps.chunks(64).flat_map(|p|bitslice(g,n,p)).collect() }
}
pub(crate) fn available()->bool{cfg!(target_arch="x86_64")}
#[cfg(target_arch="x86_64")]
#[target_feature(enable="sse2")]
unsafe fn x86(g:&[u8],n:u32,ps:&[Signed])->Vec<Signed>{
 use std::arch::x86_64::*;
 let mut xx=[[0u64;2];64];let mut zz=[[0u64;2];64];let mut rr=[0u64;2];
 for (j,&(x,z,s)) in ps.iter().enumerate(){
  let k=j/64;let bit=1u64<<(j%64);
  if s!=0{rr[k]|=bit;}
  for i in 0..n as usize{if x>>i&1!=0{xx[i][k]|=bit;}if z>>i&1!=0{zz[i][k]|=bit;}}
 }
 let mut x=[_mm_setzero_si128();64];let mut z=x;
 for i in 0..n as usize{x[i]=_mm_set_epi64x(xx[i][1] as i64,xx[i][0] as i64);z[i]=_mm_set_epi64x(zz[i][1] as i64,zz[i][0] as i64);}
 let mut r=_mm_set_epi64x(rr[1] as i64,rr[0] as i64);
 for v in g.chunks_exact(3).rev(){
  let a=v[1] as usize;let b=v[2] as usize;let xa=x[a];let za=z[a];
  match v[0]{
   0=>{r=_mm_xor_si128(r,_mm_and_si128(xa,za));x[a]=za;z[a]=xa;},
   1=>{r=_mm_xor_si128(r,_mm_andnot_si128(za,xa));z[a]=_mm_xor_si128(za,xa);},
   2=>{r=_mm_xor_si128(r,_mm_and_si128(xa,za));z[a]=_mm_xor_si128(za,xa);},
   3=>r=_mm_xor_si128(r,za),4=>r=_mm_xor_si128(r,xa),
   5=>{let xb=x[b];let zb=z[b];r=_mm_xor_si128(r,_mm_andnot_si128(_mm_xor_si128(xb,za),_mm_and_si128(xa,zb)));x[b]=_mm_xor_si128(xb,xa);z[a]=_mm_xor_si128(za,zb);},
   _=>unreachable!("Clifford admission"),
  }
 }
 for i in 0..n as usize{
  xx[i]=[_mm_cvtsi128_si64(x[i]) as u64,_mm_cvtsi128_si64(_mm_srli_si128::<8>(x[i])) as u64];
  zz[i]=[_mm_cvtsi128_si64(z[i]) as u64,_mm_cvtsi128_si64(_mm_srli_si128::<8>(z[i])) as u64];
 }
 rr=[_mm_cvtsi128_si64(r) as u64,_mm_cvtsi128_si64(_mm_srli_si128::<8>(r)) as u64];
 ps.iter().enumerate().map(|(j,_)|{
  let k=j/64;let b=j%64;let(mut a,mut z)=(0,0);
  for i in 0..n as usize{a|=((xx[i][k]>>b)&1)<<i;z|=((zz[i][k]>>b)&1)<<i;}
  (a,z,((rr[k]>>b)&1) as u8)
 }).collect()
}
