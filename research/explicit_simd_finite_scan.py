"""Explicit AVX2 feasibility, using the same full binding diagnostic as #385."""
import argparse,ctypes,json,math,platform,subprocess,tempfile
from pathlib import Path
import numpy as np
from research.native_finite_scan import ROOT,compile_kernels,validate_kernels,evaluate

def load_avx2(directory):
    if platform.machine() not in ("x86_64","AMD64"):
        return None,"non-x86-64 host"
    out=Path(directory)/"avx2.so"
    subprocess.run(["c++","-O3","-std=c++17","-shared","-fPIC","-fno-fast-math",
                    str(ROOT/"native_finite_scan"/"finite_avx2.cpp"),"-o",str(out)],check=True,timeout=90)
    lib=ctypes.CDLL(str(out))
    supported=lib.avx2_supported;supported.argtypes=[];supported.restype=ctypes.c_int
    if not supported():return None,"AVX2 unavailable"
    fn=lib.finite_scan
    fn.argtypes=[np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags="C_CONTIGUOUS"),ctypes.c_size_t]
    fn.restype=ctypes.c_int
    return fn,"AVX2 explicitly enabled after CPUID"

def extra_cases(fn):
    count=0
    # Exercise all vector-tail lengths and deliberately unaligned starts.
    patterns=[0,0x8000000000000000,1,0x7fefffffffffffff,
              0x7ff0000000000000,0xfff0000000000000,
              0x7ff8000000000001,0x7ff0000000000001]
    for size in range(1,18):
        for pos in range(size):
            for pattern in patterns:
                raw=np.zeros(size+1,dtype=np.uint64);raw[pos+1]=pattern
                x=raw[1:].view(np.float64)
                wanted=all((int(v)&0x7ff0000000000000)!=0x7ff0000000000000 for v in raw[1:])
                assert fn(x,x.size)==int(wanted)
                count+=1
    rng=np.random.default_rng(1105)
    for size in (31,64,257,1536):
        bits=rng.integers(0,np.iinfo(np.uint64).max,size=size,dtype=np.uint64)
        x=bits.view(np.float64)
        wanted=all((int(v)&0x7ff0000000000000)!=0x7ff0000000000000 for v in bits)
        assert fn(x,x.size)==int(wanted);count+=1
    return count

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=20)
    a=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        avx2,status=load_avx2(tmp)
        if avx2 is None:
            record=dict(status="UNSUPPORTED",reason=status,rows=[])
        else:
            kernels=compile_kernels(tmp);kernels["avx2"]=avx2
            cases=validate_kernels(kernels);extra=extra_cases(avx2)
            rows=[evaluate(n,l,kernels,a.repetitions) for n in (4,8,12) for l in (4,16,64)]
            record=dict(status="PASS",dispatch=status,fault_cases=cases,bit_pattern_cases=extra,
                scope="shared CI, explicit AVX2 vs scalar/native/NumPy; full extraction and phase validation retained",
                cpu=platform.machine(),compiler=subprocess.check_output(["c++","--version"],text=True).splitlines()[0],rows=rows)
    for row in record["rows"]:print(json.dumps(row,allow_nan=False),flush=True)
    print(json.dumps({k:v for k,v in record.items() if k!="rows"},allow_nan=False),flush=True)
    a.output.write_text(json.dumps(record,indent=2,allow_nan=False))
if __name__=="__main__":main()
