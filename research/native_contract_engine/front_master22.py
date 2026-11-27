"""R22: exact persistent tableau, native parallelism and matched setup/query costs."""
import json,random,sys
from itertools import product
from common5 import circuit,measure,bits
from benchmark import label
from native9 import RustSession
from planner19 import independent_image
import ketary_native_research as rn

def pack(gs):return bytes(v for g in gs for v in g)
def gen(n,count,seed):
    rng=random.Random(seed);rows=[]
    for _ in range(count):
        a,b=rng.sample(range(n),2);op=rng.randrange(6);rows.append((op,a,b if op==5 else 0))
    return rows
def native_image(s,p):
    r=s.propagate(p)
    assert r.denominator_power==0 and len(r.terms)==1
    x,z,a,b=r.terms[0];assert b==0 and abs(a)==1
    return x,z,int(a<0)
def reject(fn):
    try:fn()
    except (ValueError,TypeError,OverflowError,rn.BudgetExceeded):return
    raise AssertionError("expected admission failure")
def exact():
    checks=0;rng=random.Random(2201)
    for op in range(6):
        for a in (0,1):
            g=pack([(op,a,1-a if op==5 else 0)]);s=RustSession(2,g);t=rn.CliffordTableau(s.native,2_000_000)
            for p in product(range(4),range(4),(0,1)):
                assert t.image(p)==native_image(s,p)==independent_image(2,g,p);checks+=1
    for n in (2,4,8,16,32,64):
        for j in range(6):
            g=pack(gen(n,256,j));s=RustSession(n,g);t=rn.CliffordTableau(s.native,2_000_000)
            ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(128))
            ref=[native_image(s,p) for p in ps]
            assert t.images(ps,1,2_000_000)==t.images(ps,4,2_000_000)==ref
            assert [t.image(p) for p in ps]==ref
            for p,expected in zip(ps[:4],ref):assert independent_image(n,g,p)==expected
            checks+=len(ps)
    s=RustSession(64,b"");t=rn.CliffordTableau(s.native,2_000_000)
    assert t.image((1<<63,1<<63,1))==(1<<63,1<<63,1)
    for f in (lambda:rn.CliffordTableau(RustSession(2,b"\x06\x00\x00").native,100),lambda:rn.CliffordTableau(s.native,1),lambda:t.image((0,0,2)),lambda:t.images((),1,100),lambda:t.images(((1,1,0),),0,100),lambda:t.images(((1,1,0),),True,100),lambda:t.images(((1,1,0),),1,1),lambda:t.images(((0,0,0),)*4097,1,2_000_000)):
        reject(f);checks+=1
    return {"checks":checks+1,"scope":"persistent inverse Clifford tableau, exact generator and randomized independent parity"}

def external():
    import stim
    from qiskit.quantum_info import Clifford,Pauli
    from external21 import stim_pauli
    rows=[];rng=random.Random(2202)
    for n in (4,16,32,64):
        for count in (256,4096):
            gs=gen(n,count,n+count);g=pack(gs);s=RustSession(n,g)
            qc=circuit(n,gs).to_qiskit()
            st=stim.Circuit()
            # Explicit identities preserve idle wire count.
            st.append("I",list(range(n)))
            for op,a,b in gs:st.append(("H","S","S_DAG","X","Z","CX")[op],[a,b] if op==5 else [a])
            def kt():return rn.CliffordTableau(s.native,2_000_000)
            def stt():return stim.Tableau.from_circuit(st).inverse()
            def qct():return Clifford(qc)
            t,tt,cl=kt(),stt(),qct()
            ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(64))
            sp=tuple(stim_pauli(n,p) for p in ps);qp=tuple(Pauli(label(n,p)) for p in ps)
            got=t.images(ps,1,2_000_000)
            assert all(tt(a)==stim_pauli(n,b) and bits(c.evolve(cl,frame="h"))==b for a,b,c in zip(sp,got,qp))
            assert [native_image(s,p) for p in ps]==got
            setup=measure({"rust_tableau":kt,"stim_tableau":stt,"qiskit_clifford":qct},reps=15)
            single=measure({"rust_tableau":lambda:t.image(ps[0]),"rust_gate_scan":lambda:native_image(s,ps[0]),"stim":lambda:tt(sp[0]),"qiskit":lambda:qp[0].evolve(cl,frame="h")},reps=41)
            batch=measure({"rust_tableau_batch":lambda:t.images(ps,1,2_000_000),"stim_loop":lambda:[tt(p) for p in sp],"qiskit_loop":lambda:[p.evolve(cl,frame="h") for p in qp]},reps=9)
            rows.append({"n":n,"gates":count,"setup":setup,"single":single,"batch64":batch})
    return {"checks":512,"rows":rows,"scope":"prepared signed images, explicit setup measured separately; result representations differ; shared host"}

def parallel():
    rows=[];rng=random.Random(2203)
    for n in (16,64):
        s=RustSession(n,pack(gen(n,4096,n)));t=rn.CliffordTableau(s.native,2_000_000)
        for count in (64,256,1024,4096):
            ps=tuple((rng.getrandbits(n),rng.getrandbits(n),0) for _ in range(count));ref=t.images(ps,1,2_000_000)
            for workers in (2,4,8):assert t.images(ps,workers,2_000_000)==ref
            rows.append({"n":n,"queries":count,"timings":measure({str(w):lambda w=w:t.images(ps,w,2_000_000) for w in (1,2,4,8)},reps=21)})
    return {"rows":rows,"scope":"native scoped thread spawn included; serial fallback under 128; no persistent pool"}
if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"exact":exact,"external":external,"parallel":parallel}[sys.argv[1]]()},indent=2,allow_nan=False))
