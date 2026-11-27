"""R31 exact extended domains; independent small dense oracle controls."""
import json,sys,random
from fractions import Fraction as F
import numpy as np
from qiskit.quantum_info import Operator,Pauli
from qualified31 import Engine,SumTransition,NoiseAfter,Correctable
from qualified30 import Transition,StateEigen
from candidate28 import Policy
from native9 import RustSession
from common5 import circuit
from benchmark import label

def pack(gs):return bytes(v for g in gs for v in g)
def domains():
    checks=0;rows=[]
    for n in (3,4,5):
        s=RustSession(n,pack([(0,0,0)]));e=Engine.prepare(s,Policy(prepare_state=True,state_fallback=True))
        x=(1,0,0);z=(0,1,0);i=(0,0,0)
        sums=SumTransition(((z,F(1,3)),(x,F(2,5))),((x,F(1,3)),(z,F(2,5))))
        mutant=SumTransition(sums.post,sums.post)
        noise=NoiseAfter(z,x,((i,3),(z,1)),4,F(1,2))
        bad=NoiseAfter(z,x,noise.entries,4,F(1))
        st=((0,3,0),(0,6,0));es=(i,(1,0,0),(2,0,0),(4,0,0))
        good=Correctable(st,es);bad_code=Correctable(st,es+((7,0,0),))
        items=(Transition(z,x),StateEigen(x),sums,mutant,noise,bad,good,bad_code)
        r=e.verify(items)
        assert [v.status for v in r]==["PASS","PASS","PASS","FAIL","PASS","FAIL","PASS","FAIL"]
        assert sum(v.reserved for v in r)<=2_000_000 and r[6].snapshots==()
        assert r[4].detail.coefficient==(1,2)
        assert all(v.status=="INCONCLUSIVE" for v in e.verify(items,max_work=1))
        assert Engine.prepare(RustSession(n,pack([(6,0,0)]))).verify((noise,))[0].status=="UNSUPPORTED"
        for bad in (NoiseAfter(z,x,((i,1),),2),Correctable(st+(st[0],),es),SumTransition(((z,True),),sums.post)):
            try:e.verify((StateEigen(x),bad))
            except (ValueError,TypeError):checks+=1
            else:raise AssertionError("preflight")
        rows.append({"n":n,"domains":[v.domain for v in r],"verdicts":[v.status for v in r]})
        checks+=13
    rng=random.Random(3101)
    for n in (2,3,4):
        for seed in range(16):
            gs=[]
            for _ in range(12):
                a,b=rng.sample(range(n),2);op=rng.randrange(6);gs.append((op,a,b if op==5 else 0))
            s=RustSession(n,pack(gs));e=Engine.prepare(s)
            u=Operator(circuit(n,gs).to_qiskit()).data
            p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            v=s.propagate(p);x,z,a,b=v.terms[0];assert b==0 and abs(a)==1
            pre=(x,z,int(a<0));noise=(rng.getrandbits(n),rng.getrandbits(n),0)
            f=F(1,2) if ((noise[0]&p[1]).bit_count()+(noise[1]&p[0]).bit_count())%2 else F(1)
            spec=NoiseAfter(pre,p,(((0,0,0),3),(noise,1)),4,f)
            P=Pauli(label(n,p)).to_matrix();N=Pauli(label(n,noise)).to_matrix()
            want=u.conj().T@(.75*P+.25*N.conj().T@P@N)@u
            assert np.max(np.abs(want-float(f)*Pauli(label(n,pre)).to_matrix()))<1e-9
            assert e.verify((spec,))[0].status=="PASS"
            wrong=NoiseAfter(pre,p,spec.entries,4,-f)
            assert e.verify((wrong,))[0].status=="FAIL"
            checks+=3
    return {"checks":checks,"rows":rows,"scope":"exact typed rational sums, Clifford then Pauli mixture, finite Pauli error set; dense noise parity"}
if __name__=="__main__":print(json.dumps({"suite":"domains",**domains()},indent=2))
