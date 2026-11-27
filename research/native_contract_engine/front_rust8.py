"""Matched Rust exact sparse C ABI; all buffers caller-owned and bounded."""
import ctypes as C
import subprocess
from common5 import *
from benchmark import ROOT
from sparse import propagate,Propagation,BudgetExceeded
from fast_sparse7 import propagate_fast
from qiskit.quantum_info import Operator,Pauli
class RustSparse:
    def __init__(self):
        self.dll=C.CDLL(str(ROOT/"sparse8.so"));self.f=self.dll.sparse_propagate
        self.f.argtypes=[C.POINTER(C.c_uint8),C.c_size_t,C.c_uint32,C.c_uint64,C.c_uint64,C.c_uint8,C.c_size_t,C.c_uint64,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64)]
        self.f.restype=C.c_int
    def run(self,p,post,*,max_terms=4096,max_work=2_000_000):
        from engine import valid_pauli
        valid_pauli(post,p.width)
        if type(max_terms) is not int or not 1<=max_terms<=4096 or type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("budget")
        buf=(C.c_uint8*len(p.packed)).from_buffer_copy(p.packed);out=(C.c_uint64*(max_terms*6))();meta=(C.c_uint64*4)()
        code=self.f(buf,len(buf)//3,p.width,*post,max_terms,max_work,out,meta)
        if code in (2,3,4):raise BudgetExceeded({2:"T-count cap",3:"term-work cap",4:"live term cap"}[code])
        if code:raise ValueError("native input")
        k,peak,work,count=meta
        def signed(lo,hi):
            x=lo|(hi<<64);return x-(1<<128) if x>>127 else x
        return Propagation(tuple((out[6*i],out[6*i+1],signed(out[6*i+2],out[6*i+3]),signed(out[6*i+4],out[6*i+5])) for i in range(count)),k,peak,work)
def compile_native():
    subprocess.run(["rustc","--edition=2021","--crate-type=cdylib","-C","opt-level=3","-C","overflow-checks=yes",str(ROOT/"sparse8.rs"),"-o",str(ROOT/"sparse8.so")],check=True)
    return RustSparse()
def outcome(fn):
    try:return fn()
    except BudgetExceeded as e:return str(e)
def main():
    rs=compile_native();rng=random.Random(818);checks=budgets=0;rows=[]
    for n in (1,2,3,4,5):
        for _ in range(40):
            gs=[]
            for j in range(40):
                op=rng.randrange(8);a=rng.randrange(n)
                if op==5 and n==1:op=0
                b=rng.choice([i for i in range(n) if i!=a]) if op==5 else 0
                gs.append((op,a,b))
            p=prepare(circuit(n,gs),allow_t=True);post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            r=rs.run(p,post);assert r==propagate(n,p.gates,post)==propagate_fast(n,p.gates,post)
            u=Operator(circuit(n,gs).to_qiskit()).data
            approx=sum(((a+b*np.sqrt(2))/(1<<r.denominator_power)*Pauli(label(n,(x,z,0))).to_matrix() for x,z,a,b in r.terms),np.zeros_like(u))
            np.testing.assert_allclose(approx,u.conj().T@Pauli(label(n,post)).to_matrix()@u,atol=1e-10);checks+=1
            for kw in ({"max_terms":1},{"max_terms":4},{"max_work":1},{"max_work":40}):
                assert outcome(lambda:rs.run(p,post,**kw))==outcome(lambda:propagate(n,p.gates,post,**kw));budgets+=1
    for n in (16,32,64):
        for t in (4,8,12):
            p=prepare(circuit(n,[(4,i%n,0) for i in range(100)]+[(6,i,0) for i in range(t)]),allow_t=True)
            for kind in ("commuting","branching"):
                post=((1<<n)-1,0,0) if kind=="branching" else (0,(1<<n)-1,0)
                assert rs.run(p,post)==propagate(n,p.gates,post)
                rows.append({"n":n,"T":t,"kind":kind,"timings":measure({"python":lambda:propagate(n,p.gates,post),"optimized_python":lambda:propagate_fast(n,p.gates,post),"rust_ffi":lambda:rs.run(p,post)},reps=7)})
    p=prepare(circuit(64,[(6,63,0)]*32),allow_t=True);assert rs.run(p,(1<<63,0,1))==propagate(64,p.gates,(1<<63,0,1))
    output({"scope":"same ordered term cap, work, coefficients and result; Rust C ABI not PyO3; prepared buffers copied per call","dense_checks":checks,"budget_checks":budgets,"rows":rows})
if __name__=="__main__":main()
