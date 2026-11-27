"""R26 independent spatial verifier, held-out connected workloads and budgets."""
import random,json,sys
from itertools import product
from qiskit.quantum_info import Operator,Pauli
import numpy as np
from common5 import circuit,measure
from benchmark import label
from native9 import RustSession
from independent20 import verify_transition
from spatial26 import verify
from planner19 import plan_transition

def pack(gs):return bytes(v for g in gs for v in g)
def reject(fn):
    try:fn()
    except (ValueError,TypeError):return
    raise AssertionError("expected rejection")

def spatial():
    checks=0;rows=[];rng=random.Random(2601)
    for n in (2,3,4,5):
        partitions=(tuple((i,) for i in range(n)),tuple(tuple(range(i,min(i+2,n))) for i in range(0,n,2)))
        for seed in range(10):
            gs=[]
            for _ in range(12):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            g=pack(gs);s=RustSession(n,g)
            post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));r=s.propagate(post)
            t=r.terms
            pre=(t[0][0],t[0][1],int(t[0][2]<0)) if len(t)==1 and t[0][3]==0 and abs(t[0][2])==1<<r.denominator_power else post
            for a in (pre,(pre[0],pre[1],pre[2]^1)):
                ref=verify_transition(n,g,a,post).status
                for part in partitions:
                    got=verify(n,g,a,post,part)
                    assert got.status==ref and got.circuit_id==s.identity
                    if got.status=="FAIL":
                        u=Operator(circuit(n,gs).to_qiskit()).data
                        w=got.witness
                        # Build product eigenstate independently in little-endian order.
                        v=np.array([1],complex)
                        for axis,sign in reversed(list(zip(w.axes,w.signs))):
                            if axis=="X":q=np.array([1,sign])/np.sqrt(2)
                            elif axis=="Y":q=np.array([1,1j*sign])/np.sqrt(2)
                            else:q=np.array([1,0]) if sign==1 else np.array([0,1])
                            v=np.kron(v,q)
                        delta=u.conj().T@Pauli(label(n,post)).to_matrix()@u-Pauli(label(n,a)).to_matrix()
                        value=(w.numerator[0]+w.numerator[1]*np.sqrt(2))/(1<<w.denominator_power)
                        assert abs(np.vdot(v,delta@v).real-value)<1e-9
                    checks+=1
    for n in (16,32,64):
        # Local T blocks have total T count above native cap, but bounded
        # local transfers. Cross-block compute/uncompute is not discarded.
        gs=[g for i in range(n) for g in [(6,i,0),(4,i,0),(7,i,0),(4,i,0)]]
        chain=[(5,i,i+1) for i in range(n-1)];gs+=chain+chain[::-1]
        g=pack(gs);s=RustSession(n,g);p=((1<<n)-1,0,0);part=tuple((i,) for i in range(n))
        a=verify(n,g,p,p,part);b=verify(n,g,(p[0],0,1),p,part)
        assert a.status=="PASS" and b.status=="FAIL" and b.witness is not None
        assert a.ledger.crossings==2*(n-1)
        assert verify(n,g,p,p,part,max_work=1).status=="INCONCLUSIVE"
        rows.append({"n":n,"gates":len(gs),"baseline":plan_transition(s,p,p).status,"positive":a.status,"mutant":b.status,"ledger":a.ledger.__dict__,"timings":measure({"spatial":lambda:verify(n,g,p,p,part)},reps=7)})
        checks+=4
    return {"checks":checks,"rows":rows,"scope":"local exact-column transfer, global sparse contraction, independent of Rust; arbitrary scalability not established"}

def budget():
    checks=0;n=4;p=(15,0,0);part=((0,1),(2,3))
    g=pack([(6,i,0) for i in range(n)])
    full=verify(n,g,p,p,part);assert full.status=="FAIL"
    for kw in ({"max_work":1},{"max_terms":1},{"max_bits":1}):
        r=verify(n,g,p,p,part,**kw);assert r.status=="INCONCLUSIVE" and r.witness is None
        assert r.ledger.used<=r.ledger.reserved;checks+=1
    for bad in (((0,1),(1,2)),((0,1,2,3),),((0,),(1,),(2,),(True,))):
        reject(lambda:verify(n,g,p,p,bad));checks+=1
    for bad in (b"x",b"\x08\x00\x00",b"\x05\x00\x00",b"\x06\x04\x00"):
        reject(lambda:verify(n,bad,p,p,part));checks+=1
    rng=random.Random(2602)
    for _ in range(100):
        malformed=bytes([rng.randrange(8,256),rng.randrange(n),0])
        reject(lambda:verify(n,malformed,p,p,part));checks+=1
    return {"checks":checks+1,"scope":"admission, work/term/coefficient bit caps; bounded counters not allocator or wall-time guarantees"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"spatial":spatial,"budget":budget}[sys.argv[1]]()},indent=2,allow_nan=False))
