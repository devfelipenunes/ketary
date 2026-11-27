"""C: exact ring adversarial and scaling; no coefficient pruning."""
import random
from common5 import *
from sparse import propagate,BudgetExceeded
from engine import product_witness,difference
from test_engine import witness_state
from qiskit.quantum_info import Operator,Pauli

def main():
    checks=0;worst=0.;rng=random.Random(773);rows=[]
    for n in (1,2,3,4,5):
        for j in range(24):
            gs=[]
            for k in range(36):
                op=rng.randrange(8);a=rng.randrange(n)
                if n==1 and op==5:op=0
                b=rng.choice([v for v in range(n) if v!=a]) if op==5 else 0
                gs.append((op,a,b))
            p=prepare(circuit(n,gs),allow_t=True);post=(rng.randrange(1<<n),rng.randrange(1<<n),rng.randrange(2))
            r=propagate(n,p.gates,post);u=Operator(circuit(n,gs).to_qiskit()).data
            target=u.conj().T@Pauli(label(n,post)).to_matrix()@u
            approx=sum(((a+b*np.sqrt(2))/(1<<r.denominator_power)*Pauli(label(n,(x,z,0))).to_matrix() for x,z,a,b in r.terms),np.zeros_like(u))
            e=float(np.max(np.abs(target-approx)));assert e<1e-10;worst=max(worst,e);checks+=1
    for n in (16,32,64):
        for t in (4,8,12,13,32,33):
            p=prepare(circuit(n,[(6,i%n,0) for i in range(t)]),allow_t=True)
            for mode in ("commute","branch"):
                ob=Obligation((0,(1<<n)-1,0),(0,(1<<n)-1,0)) if mode=="commute" else Obligation(((1<<n)-1,0,0),((1<<n)-1,0,0))
                r=verify(p,(ob,))[0]
                expected="INCONCLUSIVE" if t>32 or (mode=="branch" and t>=13) else "PASS" if mode=="commute" else "FAIL"
                assert r.status==expected
                rows.append({"n":n,"t":t,"mode":mode,"status":r.status,"timings":measure({"report":lambda:verify(p,(ob,))})})
    for n in (1,16,64):
        p=prepare(circuit(n,[(6,0,0),(7,0,0)]*16),allow_t=True)
        for post in ((1,0,0),(1,1,1),(0,1,0)):
            r=propagate(n,p.gates,post);assert not difference(r.terms,r.denominator_power,post)
            assert all(max(abs(a).bit_length(),abs(b).bit_length())<=64 for _,_,a,b in r.terms)
    output({"scope":"integer exact coefficient propagation; bounded 32 T/Tdg, work and live terms; no formal proof or approximate bound","dense_checks":checks,"max_float_oracle_error":worst,"cancellation_checks":9,"rows":rows})
if __name__=="__main__":main()
