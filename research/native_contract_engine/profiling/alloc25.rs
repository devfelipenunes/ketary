//! Standalone allocation experiment, not linked into Python extension.
//! Counts requested bytes, not allocator metadata/RSS. Single threaded.
//! System is the allocator; pointers are forwarded without inspection.
use std::alloc::{GlobalAlloc,Layout,System};
use std::sync::atomic::{AtomicUsize,Ordering::Relaxed};
#[path="../pyo3/src/core.rs"] mod core;
struct Count;
static LIVE:AtomicUsize=AtomicUsize::new(0);
static PEAK:AtomicUsize=AtomicUsize::new(0);
static CALLS:AtomicUsize=AtomicUsize::new(0);
fn add(n:usize){let v=LIVE.fetch_add(n,Relaxed)+n;PEAK.fetch_max(v,Relaxed);CALLS.fetch_add(1,Relaxed);}
unsafe impl GlobalAlloc for Count{
 unsafe fn alloc(&self,l:Layout)->*mut u8{
  // SAFETY: delegate the caller's valid GlobalAlloc layout to System.
  let p=unsafe{System.alloc(l)};if !p.is_null(){add(l.size());}p
 }
 unsafe fn alloc_zeroed(&self,l:Layout)->*mut u8{
  let p=unsafe{System.alloc_zeroed(l)};if !p.is_null(){add(l.size());}p
 }
 unsafe fn dealloc(&self,p:*mut u8,l:Layout){
  LIVE.fetch_sub(l.size(),Relaxed);unsafe{System.dealloc(p,l);}
 }
 unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{
  let r=unsafe{System.realloc(p,l,n)};
  if !r.is_null(){LIVE.fetch_sub(l.size(),Relaxed);add(n);}r
 }
}
#[global_allocator] static ALLOC:Count=Count;
fn main(){
 let mut rows=Vec::with_capacity(12);
 for n in [4u32,16,32,64]{
  for t in [0usize,4,8]{
   let mut g=Vec::new();
   for i in 0..512u32{let a=(i%n) as u8;let b=((i+1)%n) as u8;g.extend_from_slice(&[5,a,b]);}
   for i in 0..t{g.extend_from_slice(&[6,(i as u32%n) as u8,0]);}
   let base=LIVE.load(Relaxed);PEAK.store(base,Relaxed);CALLS.store(0,Relaxed);
   let mask=if n==64{u64::MAX}else{(1u64<<n)-1};
   let r=core::run(&g,n,mask,0,0,4096,2_000_000).expect("bounded kernel");
   let terms=r.0.len();let peak=PEAK.load(Relaxed)-base;let retained=LIVE.load(Relaxed)-base;let calls=CALLS.load(Relaxed);
   drop(r);assert_eq!(LIVE.load(Relaxed),base);
   rows.push((n,t,terms,peak,retained,calls));
  }
 }
 println!("{{\"scope\":\"standalone core requested allocation bytes, excludes allocator metadata and Python\",\"rows\":[");
 for (i,(n,t,terms,peak,retained,calls)) in rows.iter().enumerate(){
  println!("{}{{\"n\":{},\"t\":{},\"terms\":{},\"peak_requested_bytes\":{},\"retained_bytes\":{},\"allocation_calls\":{}}}",if i==0{""}else{","},n,t,terms,peak,retained,calls);
 }
 println!("]}}");
}
