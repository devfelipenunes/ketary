"""Round 7 A: exact sparse output parity, independent dense oracle, timed kernels."""
from common5 import *
from sparse import propagate,BudgetExceeded
from fast_sparse7 import propagate_fast
from qiskit.quantum_info import Operator,Pauli

def status(f,n,gs,p,kw):
    try:return f(n,gs,p,**kw)
    except BudgetExceeded as e:return str(e)

def main():
    rng=random.Random(20261127);checks=budgets=0;worst=0.;rows=[]
    for n in (1,2,3,4,5):
        for _ in range(60):
            gs=[]
            for j in range(40):
                op=rng.randrange(8);a=rng.randrange(n)
                if op==5 and n==1:op=0
                b=rng.choice([i for i in range(n) if i!=a]) if op==5 else 0
                gs.append((op,a,b))
            p=prepare(circuit(n,gs),allow_t=True);post=(rng.randrange(1<<n),rng.randrange(1<<n),rng.randrange(2))
            r=propagate_fast(n,p.gates,post);assert r==propagate(n,p.gates,post)
            u=Operator(circuit(n,gs).to_qiskit()).data
            actual=sum(((a+b*np.sqrt(2))/(1<<r.denominator_power)*Pauli(label(n,(x,z,0))).to_matrix() for x,z,a,b in r.terms),np.zeros_like(u))
            e=float(np.max(np.abs(actual-u.conj().T@Pauli(label(n,post)).to_matrix()@u)));assert e<1e-10;worst=max(worst,e);checks+=1
            for kw in ({"max_terms":1},{"max_terms":4},{"max_work":1},{"max_work":40}):
                assert status(propagate,n,p.gates,post,kw)==status(propagate_fast,n,p.gates,post,kw);budgets+=1
    for n in (16,32,64):
        for t in (4,8,12):
            for kind in ("branching","commuting"):
                p=prepare(circuit(n,[(4,i%n,0) for i in range(100)]+[(6,i,0) for i in range(t)]),allow_t=True)
                post=((1<<n)-1,0,0) if kind=="branching" else (0,(1<<n)-1,0)
                assert propagate(n,p.gates,post)==propagate_fast(n,p.gates,post)
                rows.append({"n":n,"T":t,"kind":kind,"timings":measure({"baseline":lambda:propagate(n,p.gates,post),"optimized":lambda:propagate_fast(n,p.gates,post)},reps=7)})
    output({"scope":"matched sparse kernel output, term/work bounds, real Ketary export prepared, no report","dense_checks":checks,"budget_checks":budgets,"max_error":worst,"rows":rows})
if __name__=="__main__":main()
