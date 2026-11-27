"""QContract B1: strengthen baselines and locate losses, not just wins.

Run with installed Alpha wheels in an isolated CPython 3.12 environment.
All timing ratios are per scenario on the same host. Numeric Pauli
propagation is never treated as a formal proof.
"""
import importlib.metadata as md
import json,random,statistics,time,sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford,Pauli,PauliList,SparsePauliOp,StabilizerState,Statevector
from qcontract import Contract,StateEigen,prepare

def measure(routes,reps=9):
    rng=random.Random(4602);out={k:[] for k in routes}
    for f in routes.values():f();f()
    for _ in range(reps):
        order=list(routes);rng.shuffle(order)
        for k in order:
            t=time.perf_counter_ns();routes[k]();out[k].append((time.perf_counter_ns()-t)/1e6)
    return {k:{"median_ms":statistics.median(v),"p95_ms":float(np.percentile(v,95)),"samples_ms":v} for k,v in out.items()}
def label(n,p):
    x,z,s=p
    return ("-" if s else "")+"".join("IZXY"[2*((x>>i)&1)+((z>>i)&1)] for i in reversed(range(n)))
def mask(p):
    return (sum(int(v)<<i for i,v in enumerate(p.x)),sum(int(v)<<i for i,v in enumerate(p.z)),int(p.phase)//2)
def random_clifford(n,gates,rng):
    c=QuantumCircuit(n)
    for _ in range(gates):
        a,b=rng.sample(range(n),2);op=rng.randrange(6)
        if op==5:c.cx(a,b)
        else:getattr(c,("h","s","sdg","x","z")[op])(a)
    return c
def qs(pres,got):
    return tuple(bool(x) for x in np.all(got.x==pres.x,axis=1)&np.all(got.z==pres.z,axis=1)&(got.phase==pres.phase))
def clifford():
    rng=random.Random(4601);rows=[];checks=0
    for n in (2,4,8,16,32,64):
        for gates in (64,512,4096):
            c=random_clifford(n,gates,rng);p=prepare(c);cl=Clifford(c);inv=cl.adjoint()
            setup=measure({"qcontract":lambda:prepare(c),"qiskit_inverse":lambda:Clifford(c).adjoint()},7)
            for density in ("sparse","dense"):
                for count in (1,8,32,64):
                    ps=tuple((1<<rng.randrange(n),1<<rng.randrange(n),rng.randrange(2)) if density=="sparse" else (rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(count))
                    posts=PauliList([label(n,x) for x in ps])
                    imgs=posts.evolve(inv,frame="s")
                    direct=posts.evolve(cl,frame="h")
                    assert np.array_equal(imgs.x,direct.x) and np.array_equal(imgs.z,direct.z) and np.array_equal(imgs.phase,direct.phase)
                    targets=tuple((a[0],a[1],a[2]^(j%2)) for j,a in enumerate(map(mask,imgs)))
                    pres=PauliList([label(n,x) for x in targets])
                    specs=tuple(Contract(requires=a,ensures=b) for a,b in zip(targets,ps))
                    want=tuple(j%2==0 for j in range(count))
                    def native():return p.verify(*specs)
                    def verdicts():return tuple(r.passed for r in native())
                    def cached():return qs(pres,posts.evolve(inv,frame="s"))
                    def original():return qs(pres,posts.evolve(cl,frame="h"))
                    assert verdicts()==cached()==original()==want
                    assert all(r.status in ("PASS","FAIL") for r in native())
                    checks+=count
                    times=measure({"qcontract_reports":native,"qcontract_verdicts":verdicts,"qiskit_inverse_prepared":cached,"qiskit_original":original,
                                   "qcontract_end_to_end":lambda:tuple(r.passed for r in prepare(c).verify(*specs)),
                                   "qiskit_inverse_end_to_end":lambda:qs(pres,posts.evolve(Clifford(c).adjoint(),frame="s"))},7)
                    rows.append({"width":n,"gates":gates,"density":density,"queries":count,"setup":setup,"timings":times})
    return {"checks":checks,"rows":rows,"scope":"matched Boolean verdicts, full report overhead additional, prepared inverse baseline and same-host end-to-end"}

def state():
    rng=random.Random(4603);rows=[];checks=0
    for n in (4,8,16,32,64):
        for family in ("ghz","random"):
            if family=="ghz":
                c=QuantumCircuit(n);c.h(0)
                for j in range(1,n):c.cx(0,j)
            else:c=random_clifford(n,256,rng)
            cl=Clifford(c);inv=cl.adjoint();st=StabilizerState(cl)
            # Include actual stabilizers, sign mutants and arbitrary Pauli.
            good=tuple(mask(Pauli(label(n,(0,1<<j,0))).evolve(cl,frame="s")) for j in range(min(n,8)))
            ps=good+tuple((x,z,s^1) for x,z,s in good)+tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(8))
            labels=[label(n,x) for x in ps];posts=PauliList(labels);single=tuple(Pauli(x) for x in labels)
            specs=tuple(StateEigen(x) for x in ps)
            p=prepare(c);dag=prepare(c,prepare_state=True)
            def inv_values():
                evolved=posts.evolve(inv,frame="s")
                return tuple(int(1-2*(int(ph)//2)) if not np.any(x) else 0 for x,ph in zip(evolved.x,evolved.phase))
            def st_values():return tuple(int(round(complex(st.expectation_value(x)).real)) for x in single)
            want=inv_values();assert st_values()==want
            def native(engine):return engine.verify(*specs)
            for eng in (p,dag):
                for r,v in zip(native(eng),want):
                    if r.status=="INCONCLUSIVE":continue
                    assert r.status==("PASS" if v==1 else "FAIL")
                    (a,b),k=r.expectation;assert b==0 and a==v*(1<<k)
                    checks+=1
            routes={"qcontract_default":lambda:native(p),"qcontract_prepared_dag":lambda:native(dag),"qiskit_inverse_values":inv_values,"qiskit_stabilizer_values":st_values}
            if n<=16:
                sv=Statevector.from_instruction(c)
                def dense():return tuple(float(sv.expectation_value(x).real) for x in single)
                assert np.allclose(dense(),want,atol=1e-9,rtol=0);routes["qiskit_dense_prepared"]=dense
            rows.append({"width":n,"family":family,"queries":len(ps),"default_decisive":sum(r.status in ("PASS","FAIL") for r in native(p)),
                         "dag_decisive":sum(r.status in ("PASS","FAIL") for r in native(dag)),
                         "setup":measure({"qcontract":lambda:prepare(c),"qcontract_dag":lambda:prepare(c,prepare_state=True),"qiskit_inverse":lambda:Clifford(c).adjoint(),"qiskit_stabilizer":lambda:StabilizerState(c)},5),
                         "timings":measure(routes,7)})
    return {"checks":checks,"rows":rows,"scope":"zero-input Clifford expectations, scalable stabilizer and prepared inverse baselines; numeric dense only <=16; record coverage"}

def near_clifford():
    from pauli_prop import propagate_through_circuit
    rng=random.Random(4604);rows=[];checks=0
    for n in (4,8,16,32,64):
        for tc in (4,8,12):
            for family in ("commuting","interleaved"):
                prefix=random_clifford(n,64,rng)
                tail=random_clifford(n,64,rng)
                mid=QuantumCircuit(n)
                for j in range(tc):
                    wire=j%n
                    if family=="interleaved":
                        mid.h(wire);mid.cx(wire,(wire+1)%n)
                    (mid.t if j%2==0 else mid.tdg)(wire)
                c=prefix.compose(mid).compose(tail)
                # Use equivalent RZ rotations for pauli-prop; the T/Tdg
                # global phase cancels from conjugation. No truncation
                # by magnitude; 2**T-count is an upper bound on terms.
                rot=QuantumCircuit(n)
                for inst in c.data:
                    wires=[c.find_bit(q).index for q in inst.qubits]
                    if inst.operation.name in ("t","tdg"):rot.rz(np.pi/4 if inst.operation.name=="t" else -np.pi/4,wires[0])
                    else:rot.append(inst.operation,wires)
                p=prepare(c)
                post=[(0,0,0),(rng.getrandbits(n),rng.getrandbits(n),0)]
                # In commuting family this observable has a known all-input
                # Pauli preimage. Interleaved family uses a fixed target;
                # arbitrary non-Pauli images may give decisive FAIL.
                middle=Pauli(label(n,(0,1,0)))
                post.append(mask(middle.evolve(Clifford(tail),frame="s")))
                pre=[(0,0,0),(1,0,0),mask(middle.evolve(Clifford(prefix).adjoint(),frame="s"))]
                specs=tuple(Contract(requires=a,ensures=b) for a,b in zip(pre,post))
                op=tuple(SparsePauliOp.from_list([(label(n,b),1)]) for b in post)
                target=tuple(SparsePauliOp.from_list([(label(n,a),1)]) for a in pre)
                def native():return p.verify(*specs)
                def numeric():return tuple(propagate_through_circuit(x,rot,max_terms=1<<tc,atol=0.0,frame="h") for x in op)
                got=native();nums=numeric();res=[]
                for r,v,t in zip(got,nums,target):
                    d=(v-t).simplify(atol=0,rtol=0)
                    residual=float(np.sum(np.abs(d.coeffs)))
                    status="NUMERIC_MATCH" if residual<1e-10 else "NUMERIC_DIFFERENT" if residual>1e-7 else "NUMERIC_UNCERTAIN"
                    if r.status in ("PASS","FAIL") and status!="NUMERIC_UNCERTAIN":
                        assert (r.status=="PASS")==(status=="NUMERIC_MATCH")
                        checks+=1
                    res.append({"native":r.status,"numeric":status,"l1_residual":residual,"terms":len(v),"route":r.route})
                assert got[0].status=="PASS"
                if family=="commuting":assert got[2].status=="PASS" or got[2].status=="INCONCLUSIVE"
                rows.append({"width":n,"t_count":tc,"family":family,"results":res,"timings":measure({"qcontract_reports":native,"pauli_prop_numeric":numeric},5)})
    return {"checks":checks,"rows":rows,"scope":"no magnitude truncation, 2^T term cap, numerical residual not proof; compare only decisive native results; numerical output vs reports"}
if __name__=="__main__":
    suite=sys.argv[1]
    print(json.dumps({"suite":suite,"versions":{k:md.version(k) for k in ("qcontract-alpha-local","qiskit","numpy","pauli-prop")},**{"clifford":clifford,"state":state,"near-clifford":near_clifford}[suite]()},indent=2,allow_nan=False))
