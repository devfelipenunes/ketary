"""Matched research benchmark with real Ketary/Qiskit and native kernels."""
import ctypes as C
import importlib.metadata as md
import json, pathlib, platform, random, statistics, time, subprocess
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford, Operator, Pauli

ROOT=pathlib.Path(__file__).resolve().parent
OPS=("h","s","sdg","x","z","cx")
RNG=random.Random(20261126)
def load(name):
    dll=C.CDLL(str(ROOT/name));f=dll.propagate
    f.argtypes=[C.POINTER(C.c_uint8),C.c_size_t,C.c_uint32,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64),C.POINTER(C.c_uint8)]
    f.restype=C.c_int
    return f
def pack(g):
    return (C.c_uint8*(3*len(g))).from_buffer_copy(bytes(v for row in g for v in row))
def invoke(f,b,n,p):
    x,z,r=C.c_uint64(p[0]),C.c_uint64(p[1]),C.c_uint8(p[2])
    status=f(b,len(b)//3,n,C.byref(x),C.byref(z),C.byref(r))
    if status:raise ValueError(status)
    return x.value,z.value,r.value
def py(g,n,p):
    x,z,r=p
    for op,a,b in reversed(g):
        A=1<<a;xa=bool(x&A);za=bool(z&A)
        if op==0:
            r^=xa&za
            if xa!=za:x^=A;z^=A
        elif op==1:
            r^=xa and not za
            if xa:z^=A
        elif op==2:
            r^=xa&za
            if xa:z^=A
        elif op==3:r^=za
        elif op==4:r^=xa
        else:
            B=1<<b;xb=bool(x&B);zb=bool(z&B);r^=xa and zb and not(xb^za)
            if xa:x^=B
            if zb:z^=A
    return x,z,r
def label(n,p):
    x,z,r=p
    return ("-" if r else "")+"".join("IZXY"[2*((x>>i)&1)+((z>>i)&1)] for i in reversed(range(n)))
def build(n,g):
    c=QuantumCircuit(n)
    for op,a,b in g:
        if op==5:c.cx(a,b)
        else:getattr(c,OPS[op])(a)
    return c
def export(c):
    native=c.to_qiskit()
    if native.num_clbits or native.num_parameters or not 1<=native.num_qubits<=64 or len(native.data)>1_000_000:
        raise ValueError("unsupported circuit")
    out=[]
    for inst in native.data:
        # Accept only canonical built-in gate base classes, not name spoofing.
        op=inst.operation
        i=OPS.index(op.name)
        from qiskit.circuit.library import HGate,SGate,SdgGate,XGate,ZGate,CXGate
        if op.base_class is not (HGate,SGate,SdgGate,XGate,ZGate,CXGate)[i] or inst.clbits or op.params:
            raise ValueError("unsupported gate")
        wires=[native.find_bit(w).index for w in inst.qubits]
        if len(wires)!=(2 if i==5 else 1):raise ValueError("arity")
        out.append((i,wires[0],wires[1] if i==5 else 0))
    return pack(out)
def random_g(n,k):
    return [(RNG.randrange(6),a,b) for a,b in (RNG.sample(range(n),2) for _ in range(k))]
def main():
    subprocess.run(["g++","-std=c++17","-O3","-shared","-fPIC",str(ROOT/"pauli.cpp"),"-o",str(ROOT/"cpp.so")],check=True)
    subprocess.run(["rustc","--edition=2021","--crate-type=cdylib","-C","opt-level=3",str(ROOT/"pauli.rs"),"-o",str(ROOT/"rust.so")],check=True)
    cpp,rust=load("cpp.so"),load("rust.so")
    checks=0
    for n,g,p in [(2,[(op,a,1-a)],(x,z,r)) for op in range(6) for a in range(2) for x in range(4) for z in range(4) for r in range(2)]+[(n,random_g(n,30),(RNG.randrange(1<<n),RNG.randrange(1<<n),RNG.randrange(2))) for n in (2,3,4,5) for _ in range(30)]:
        c=build(n,g);u=Operator(c).data;pr=Pauli(label(n,p));b=pack(g)
        expected=py(g,n,p)
        for f in (cpp,rust):
            got=invoke(f,b,n,p);assert got==expected
            np.testing.assert_allclose(Pauli(label(n,got)).to_matrix(),u.conj().T@pr.to_matrix()@u,atol=1e-10)
            assert Pauli(label(n,got))==pr.evolve(c,frame="h")
            checks+=1
    for f in (cpp,rust):
        for g,n,p in [([(5,0,0)],2,(0,1,0)), ([(0,64,0)],64,(0,1,0)), ([(6,0,1)],2,(0,1,0)), ([(0,0,0)],2,(0,1,2))]:
            try:invoke(f,pack(g),n,p)
            except ValueError:pass
            else:raise AssertionError("accepted invalid input")
        assert invoke(f,pack([(3,63,0)]),64,(0,1<<63,0))==(0,1<<63,1)
    rows=[]
    for n in (4,16,32):
        for k in (100,1000,10000):
            g=random_g(n,k);c=q.from_qiskit(build(n,g));qc=c.to_qiskit();b=export(c)
            p=(RNG.getrandbits(n),RNG.getrandbits(n),RNG.randrange(2))
            pr=Pauli(label(n,p));cl=Clifford(qc);expected=py(g,n,p)
            assert bytes(b)==bytes(pack(g))
            assert invoke(cpp,b,n,p)==invoke(rust,b,n,p)==expected
            assert pr.evolve(qc,frame="h")==pr.evolve(cl,frame="h")==Pauli(label(n,expected))
            methods={"python_kernel":lambda:py(g,n,p),"cpp_prepacked":lambda:invoke(cpp,b,n,p),"rust_prepacked":lambda:invoke(rust,b,n,p),
                     "cpp_ketary_export":lambda:invoke(cpp,export(c),n,p),"rust_ketary_export":lambda:invoke(rust,export(c),n,p),
                     "qiskit_clifford_prebuilt":lambda:pr.evolve(cl,frame="h"),
                     "qiskit_circuit":lambda:pr.evolve(qc,frame="h"),
                     "qiskit_ketary_export":lambda:pr.evolve(c.to_qiskit(),frame="h")}
            raw={m:[] for m in methods}
            for fn in methods.values():
                for _ in range(3):fn()
            for _ in range(21):
                order=list(methods);RNG.shuffle(order)
                for m in order:
                    t=time.perf_counter_ns();methods[m]();raw[m].append((time.perf_counter_ns()-t)/1e6)
            rows.append({"qubits":n,"gates":k,"median_ms":{m:statistics.median(v) for m,v in raw.items()},"p95_ms":{m:float(np.percentile(v,95)) for m,v in raw.items()},"samples_ms":raw})
    print(json.dumps({"scope":"research Clifford Pauli conjugation, not general circuit equivalence or whole contract report; export paths include canonical gate validation","checks":checks,"repetitions":21,"python":platform.python_version(),"versions":{p:md.version(p) for p in ("ketary","qiskit","numpy")},"rustc":subprocess.check_output(["rustc","--version"],text=True).strip(),"cpp":subprocess.check_output(["g++","--version"],text=True).splitlines()[0],"rows":rows},indent=2,allow_nan=False))
if __name__=="__main__":main()
