//! Research-only Clifford Pauli conjugation. C ABI for matched benchmark,
//! not a Python extension or a public Ketary runtime dependency.
#[no_mangle]
pub unsafe extern "C" fn propagate(gates:*const u8,count:usize,n:u32,
    x:*mut u64,z:*mut u64,r:*mut u8)->i32 {
    if gates.is_null() || x.is_null() || z.is_null() || r.is_null()
        || n==0 || n>64 || count>1_000_000 {return 1;}
    // Caller must own valid non-overlapping buffers of the documented lengths.
    let (mut xx,mut zz,mut rr)=(*x,*z,*r);
    if rr>1 || (n<64 && ((xx|zz)>>n)!=0){return 1;}
    let g=std::slice::from_raw_parts(gates,3*count);
    for v in g.chunks_exact(3).rev(){
        let (op,a,b)=(v[0],u32::from(v[1]),u32::from(v[2]));
        if op>5 || a>=n || (op==5 && (b>=n || a==b)){return 2;}
        let aa=1u64<<a;
        let (xa,za)=((xx&aa)!=0,(zz&aa)!=0);
        match op {
            0=>{rr^=(xa&&za) as u8;if xa!=za{xx^=aa;zz^=aa;}},
            1=>{rr^=(xa&&!za) as u8;if xa{zz^=aa;}},
            2=>{rr^=(xa&&za) as u8;if xa{zz^=aa;}},
            3=>rr^=za as u8,
            4=>rr^=xa as u8,
            5=>{let bb=1u64<<b;let(xb,zb)=((xx&bb)!=0,(zz&bb)!=0);
                rr^=(xa&&zb&&!(xb^za)) as u8;if xa{xx^=bb;}if zb{zz^=aa;}},
            _=>return 2,
        }
    }
    *x=xx;*z=zz;*r=rr;0
}
