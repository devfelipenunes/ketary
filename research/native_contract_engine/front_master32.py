"""R32 matched performance experiment. Raw and normalized outputs separate.
No speed gate based on noisy shared runners; exact parity is mandatory.
"""
import json,random,sys,struct,importlib.metadata as md
import numpy as np
from qiskit.quantum_info import Clifford,Pauli,PauliList,Statevector,Operator
from common5 import circuit,measure,bits
from benchmark import label
from native9 import RustSession
from qualified31 import Engine
from qualified30 import Transition,StateEigen,Equivalent
from candidate28 import Policy
from state29 import verify as heisenberg
from front_master22 import gen,pack
from planner19 import independent_image
import ketary_native_research as rn

RECORD=struct.Struct("<QQB")
def encode(ps):return b"".join(RECORD.pack(*p) for p in ps)
def decode(raw):return tuple(RECORD.iter_unpack(raw))
def qbytes(ps):
    # Normalize Qiskit's vectorized native representation to the same
    # fixed-width wire/mask/sign bytes as the native packed API.
    m=len(ps);out=np.zeros((m,17),np.uint8)
    x=np.packbits(ps.x,axis=1,bitorder="little");z=np.packbits(ps.z,axis=1,bitorder="little")
    out[:,:x.shape[1]]=x;out[:,8:8+z.shape[1]]=z
    phase=np.asarray(ps.phase);assert np.all((phase==0)|(phase==2))
    out[:,16]=phase//2
    return out.tobytes()

def exact():
    rng=random.Random(3201);checks=0;rows=[]
    for n in (2,3,4,5,7,8,15,16,31,32,63,64):
        s=RustSession(n,pack(gen(n,256,n+3201)));t=rn.CliffordTableau(s.native,2_000_000);l=rn.CliffordLookup(t,2_000_000)
        ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(128))
        ref=tuple(t.images(ps,1,2_000_000))
        assert tuple(l.images(ps,2_000_000))==ref and decode(l.packed_images(encode(ps),2_000_000))==ref
        assert all(l.image(p)==r for p,r in zip(ps,ref))
        for p,r in zip(ps[:4],ref):assert independent_image(n,s.packed,p)==r
        checks+=128
        e=Engine.prepare(s)
        specs=tuple(Transition(r if i%2==0 else (r[0],r[1],r[2]^1),p) for i,(p,r) in enumerate(zip(ps[:64],ref)))
        for budget in (1,64,64*(6*n+6),64*(6*n+7),2_000_000):
            q=budget//len(specs);got=e.verify(specs,max_work=budget)
            if q:
                old=tuple(e.verify((spec,),max_work=q)[0] for spec in specs)
                assert got==old
            else:assert all(r.status=="INCONCLUSIVE" for r in got)
            checks+=len(specs)
        rows.append({"n":n,"lookup_storage_bytes":l.storage_bytes(),"tableau_payload_bytes":t.storage_bytes()[1]})
    t=rn.CliffordTableau(RustSession(2,b"").native,1000);l=rn.CliffordLookup(t,1000)
    for f in (lambda:l.packed_images(b"",1000),lambda:l.packed_images(b"x",1000),lambda:l.packed_images(encode(((4,0,0),)),1000),lambda:l.packed_images(encode(((0,0,2),)),1000),lambda:l.packed_images(encode(((0,0,0),))*4097,2_000_000),lambda:l.packed_images(encode(((0,0,0),)),1),lambda:l.image((True,0,0)),lambda:rn.CliffordLookup(t,1)):
        try:f()
        except (ValueError,TypeError,OverflowError,rn.BudgetExceeded):checks+=1
        else:raise AssertionError("malformed or overbudget request accepted")
    return {"checks":checks,"rows":rows,"scope":"strict packed and tuple parity, partial widths, independent reference, facade batching and budget boundaries"}

def clifford():
    import stim
    from external21 import stim_pauli
    rng=random.Random(3202);rows=[];checks=0
    for n in (4,16,32,64):
        for gates in (256,4096):
            gs=gen(n,gates,n+gates+3202);g=pack(gs);k=circuit(n,gs);qc=k.to_qiskit()
            s=RustSession(n,g)
            def base():return rn.CliffordTableau(s.native,2_000_000)
            def lookup():return rn.CliffordLookup(base(),2_000_000)
            t=base();l=rn.CliffordLookup(t,2_000_000);cl=Clifford(qc)
            st=stim.Circuit();st.append("I",list(range(n)))
            for op,a,b in gs:st.append(("H","S","S_DAG","X","Z","CX")[op],[a,b] if op==5 else [a])
            stt=stim.Tableau.from_circuit(st).inverse()
            setup=measure({"tableau":base,"lookup_total":lookup,"lookup_incremental":lambda:rn.CliffordLookup(t,2_000_000),"qiskit":lambda:Clifford(qc),"stim":lambda:stim.Tableau.from_circuit(st).inverse(),"snapshot_from_sdk":lambda:RustSession.from_circuit(k)},reps=11)
            for density in ("sparse","dense"):
                for count in (1,64,1024):
                    ps=tuple(((1<<rng.randrange(n),1<<rng.randrange(n),rng.randrange(2)) if density=="sparse" else (rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))) for _ in range(count))
                    raw=encode(ps);ql=PauliList([label(n,p) for p in ps]);sp=tuple(stim_pauli(n,p) for p in ps)
                    expected=tuple(t.images(ps,1,2_000_000));exp=encode(expected)
                    assert l.packed_images(raw,2_000_000)==qbytes(ql.evolve(cl,frame="h"))==exp
                    assert tuple(l.images(ps,2_000_000))==expected
                    assert all(stt(a)==stim_pauli(n,b) for a,b in zip(sp,expected));checks+=count
                    timing=measure({"tableau_tuple":lambda:t.images(ps,1,2_000_000),"lookup_tuple":lambda:l.images(ps,2_000_000),"lookup_packed":lambda:l.packed_images(raw,2_000_000),"qiskit_vectorized":lambda:ql.evolve(cl,frame="h"),"qiskit_to_packed":lambda:qbytes(ql.evolve(cl,frame="h")),"stim_loop":lambda:[stt(a) for a in sp]},reps=15)
                    row={"n":n,"gates":gates,"density":density,"queries":count,"timings":timing,"setup":setup,"lookup_payload":l.storage_bytes()}
                    if count==64:
                        e=Engine.prepare(s);specs=tuple(Transition(a,p) for a,p in zip(expected,ps))
                        assert all(r.status=="PASS" for r in e.verify(specs))
                        row["facade"]=measure({"batched_reports":lambda:e.verify(specs),"single_reports":lambda:tuple(e.verify((x,),max_work=2_000_000//64)[0] for x in specs)},reps=11)
                    rows.append(row)
    return {"checks":checks,"rows":rows,"versions":{p:md.version(p) for p in ("qiskit","stim")},"scope":"prepared signed Pauli images; same output bytes for packed pair; setup and full report costs separated; input representations already prepared; shared host"}

def state():
    rng=random.Random(3203);rows=[];checks=0
    for n in (4,8,12,16,20):
        for family in ("ghz","brickwork"):
            if family=="ghz":gs=[(0,0,0)]+[(5,0,i) for i in range(1,n)]
            else:
                gs=[(0,i,0) for i in range(n)]
                for layer in range(4):
                    gs.extend((rng.choice((0,1,2,3,4,6,7)),i,0) for i in range(n))
                    gs.extend((5,i,i+1) for i in range(layer%2,n-1,2))
            s=RustSession(n,pack(gs));qc=circuit(n,gs).to_qiskit()
            dense=Statevector.from_instruction(qc);e=Engine.prepare(s,Policy(state_fallback=True))
            ps=((0,0,0),(0,0,1),((1<<n)-1,0,0))+tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(5))
            qp=tuple(Pauli(label(n,p)) for p in ps)
            got=[heisenberg(s,p) for p in ps];specs=tuple(StateEigen(p) for p in ps)
            for p,r,ref in zip(qp,got,e.verify(specs)):
                if r.status=="INCONCLUSIVE":continue
                (a,b),k=r.expectation;want=float(dense.expectation_value(p).real)
                assert abs((a+b*np.sqrt(2))/(1<<k)-want)<1e-8
                if ref.status!="INCONCLUSIVE":assert ref.detail.expectation==r.expectation
                checks+=1
            def dense_queries(v):return [float(v.expectation_value(p).real) for p in qp]
            timing=measure({"native_expectation":lambda:[heisenberg(s,p) for p in ps],"native_reports":lambda:e.verify(specs),"qiskit_prepared":lambda:dense_queries(dense),"qiskit_end_to_end":lambda:dense_queries(Statevector.from_instruction(qc))},reps=7 if n<=16 else 3)
            rows.append({"n":n,"family":family,"gates":len(gs),"decisive":sum(r.status!="INCONCLUSIVE" for r in got),"queries":len(ps),"timings":timing,"dense_bytes":dense.data.nbytes})
    return {"checks":checks,"rows":rows,"scope":"zero-input expectations only; exact native versus numerical dense; report inconclusive coverage; preparation excluded/included separately"}

def equivalence():
    from mqt import qcec
    rows=[];checks=0
    for n in (4,8,16,32):
        for family in ("clifford","clifford-t"):
            gs=gen(n,128,n+3204)
            if family=="clifford-t":gs.extend((6,i,0) for i in range(min(n,4)))
            g=pack(gs);s=RustSession(n,g);e=Engine.prepare(s);a=circuit(n,gs).to_qiskit()
            for mutate in (False,True):
                hs=gs+([(3,0,0)] if mutate else [(5,0,1),(5,0,1)])
                ref=RustSession(n,pack(hs));b=circuit(n,hs).to_qiskit();spec=Equivalent(ref)
                want="FAIL" if mutate else "PASS";r=e.verify((spec,))[0];assert r.status in (want,"INCONCLUSIVE")
                def external():return qcec.verify(a,b)
                ext=str(external().equivalence).split(".")[-1]
                if ext in ("equivalent","equivalent_up_to_global_phase","not_equivalent"):assert (ext=="not_equivalent")==mutate
                routes={"native_report":lambda:e.verify((spec,)),"qcec_end_to_end":external}
                if n<=8:
                    u,v=Operator(a),Operator(b);assert u.equiv(v)==(not mutate)
                    routes["qiskit_prepared"]=lambda:u.equiv(v)
                    routes["qiskit_end_to_end"]=lambda:Operator(a).equiv(Operator(b))
                rows.append({"n":n,"family":family,"mutant":mutate,"native_status":r.status,"qcec_status":ext,"timings":measure(routes,reps=5)})
                checks+=1
    return {"checks":checks,"rows":rows,"scope":"full unitary equivalence up to phase, exact native vs numerical or portfolio; no speed claim for inconclusive results"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"exact":exact,"clifford":clifford,"state":state,"equivalence":equivalence}[sys.argv[1]]()},indent=2,allow_nan=False))
