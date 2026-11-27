"""R28 integrated exact domains, held-out entangled workloads, budget controls."""
import json,random,sys
from dataclasses import replace
import numpy as np
from qiskit.quantum_info import Statevector,Pauli
from benchmark import label
from common5 import circuit,measure
from native9 import RustSession
from candidate28 import Engine,Policy,Transition,StateEigen,replay_report
from independent20 import verify_transition
from weighted27 import simulate as weighted
from dag22 import simulate as plain

def pack(gs):return bytes(v for g in gs for v in g)
def reject(f):
    try:f()
    except (ValueError,TypeError):return
    raise AssertionError("expected rejection")
def integrated():
    checks=0;rows=[]
    for n in (2,4,8,16,32,64):
        gs=[(0,0,0)]+[(5,0,i) for i in range(1,n)]
        s=RustSession(n,pack(gs));p=((1<<n)-1,0,0)
        specs=(Transition((0,1,0),p),StateEigen(p),Transition((1,0,0),p),StateEigen((0,1,0)))
        e=Engine(s,Policy(prepare_state=True))
        b=e.verify(specs)
        # GHZ preparation maps input X_0 to global X after the CXs only;
        # including initial H gives input Z_0.
        assert [r.status for r in b.reports]==["PASS","PASS","FAIL","FAIL"]
        assert b.query_reserved==b.transition_reserved+b.state_reserved<=2_000_000
        assert b.reports[0].domain!=b.reports[1].domain
        for i in (1,3):
            assert replay_report(s,specs[i],b.reports[i]) is True
            assert replay_report(s,specs[i],replace(b.reports[i],status="FAIL" if i==1 else "PASS")) is False
            assert replay_report(s,specs[0],b.reports[i]) is False
            checks+=3
        assert all(r.status=="INCONCLUSIVE" for r in e.verify(specs,max_work=1).reports)
        w=Engine(s,Policy(prepare_state=True,state_backend="phase-weighted"))
        assert [r.status for r in w.verify(specs).reports]==[r.status for r in b.reports]
        assert Engine(s).verify((specs[1],)).reports[0].status=="INCONCLUSIVE"
        rows.append({"n":n,"routes":[r.route for r in b.reports],"timings":measure({"mixed_query":lambda:e.verify(specs)},reps=9)})
        checks+=7
    # Same state property does not imply all-input invariant.
    e=Engine(RustSession(1,pack([(0,0,0)])),Policy(prepare_state=True))
    assert [r.status for r in e.verify((StateEigen((1,0,0)),Transition((1,0,0),(1,0,0)))).reports]==["PASS","FAIL"]
    reject(lambda:e.verify((StateEigen((True,0,0)),)))
    reject(lambda:Engine(e.session,Policy(state_backend="auto")))
    return {"checks":checks+3,"rows":rows,"scope":"private typed exact transition and state domains, separate preparation reservations"}

def graph(n,seed):
    rng=random.Random(seed);gs=[(0,i,0) for i in range(n)];edges=set()
    # A connected ring with random long-range chords; CZ compiled into H/CX/H.
    for i in range(n):edges.add(tuple(sorted((i,(i+1)%n))))
    for _ in range(n//2):edges.add(tuple(sorted(rng.sample(range(n),2))))
    for a,b in sorted(edges):gs.extend([(0,b,0),(5,a,b),(0,b,0)])
    # T only on even vertices; odd graph stabilizers still commute with T.
    gs.extend((6,i,0) for i in range(0,n,2))
    obs=[]
    for i in range(1,n,2):
        mask=sum(1<<(b if a==i else a) for a,b in edges if i in (a,b))
        obs.append((i,(1<<i,mask,0)))
    return gs,obs

def workloads():
    checks=0;rows=[];rng=random.Random(2801)
    for n in (6,8,10,12):
        for depth in (2,4,8):
            for seed in range(3):
                gs=[(0,i,0) for i in range(n)]
                for layer in range(depth):
                    for i in range(n):
                        op=rng.choice((0,1,2,3,4,6,7));gs.append((op,i,0))
                    for i in range(layer%2,n-1,2):gs.append((5,i,i+1))
                    gs.append((5,n-1,0))
                g=pack(gs);s=RustSession(n,g);qc=circuit(n,gs).to_qiskit()
                dense=Statevector.from_instruction(qc)
                # Positive and negative cases plus potentially hard random observables.
                ps=((0,0,0),(0,0,1))+tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(6))
                specs=tuple(StateEigen(p) for p in ps)
                a=Engine(s,Policy(prepare_state=True));b=Engine(s,Policy(prepare_state=True,state_backend="phase-weighted"))
                ra=a.verify(specs);rb=b.verify(specs)
                for p,x,y in zip(ps,ra.reports,rb.reports):
                    expected=float(dense.expectation_value(Pauli(label(n,p))).real)
                    for r in (x,y):
                        if r.status=="INCONCLUSIVE":continue
                        (u,v),k=r.expectation
                        assert abs((u+v*np.sqrt(2))/(1<<k)-expected)<1e-8
                        assert r.status==("PASS" if abs(expected-1)<1e-9 else "FAIL")
                        checks+=1
                    if x.expectation is not None and y.expectation is not None:assert x.expectation==y.expectation
                rows.append({"family":"brickwork","n":n,"depth":depth,"seed":seed,"gates":len(gs),"plain_nodes":None if a.state is None else len(a.state.nodes),"weighted_nodes":None if b.state is None else len(b.state.nodes),"plain_decisive":sum(r.status!="INCONCLUSIVE" for r in ra.reports),"weighted_decisive":sum(r.status!="INCONCLUSIVE" for r in rb.reports)})
    for n in (8,16,32,64):
        gs,obs=graph(n,2802+n);g=pack(gs);s=RustSession(n,g)
        e=Engine(s,Policy(prepare_state=True,state_backend="phase-weighted"))
        # One stabilizer and its sign mutant, not a compute/uncompute identity.
        i,p=obs[len(obs)//2];pre=(0,1<<i,0)
        specs=(Transition(pre,p),Transition((0,1<<i,1),p),StateEigen(p),StateEigen((p[0],p[1],1)))
        b=e.verify(specs)
        for r,want in zip(b.reports,("PASS","FAIL","PASS","FAIL")):
            assert r.status in (want,"INCONCLUSIVE")
            if r.status==want:checks+=1
        if n==8:assert [r.status for r in b.reports]==["PASS","FAIL","PASS","FAIL"]
        rows.append({"family":"T-dressed chordal ring graph","n":n,"gates":len(gs),"state_nodes":None if e.state is None else len(e.state.nodes),"verdicts":[r.status for r in b.reports],"routes":[r.route for r in b.reports]})
    return {"checks":checks,"rows":rows,"scope":"held-out interacting circuits; report inconclusive coverage, no general scaling claim"}

def admission():
    s=RustSession(2,b"");e=Engine(s,Policy(prepare_state=True))
    p=(1,0,0);q=(0,0,0);checks=0
    for f in (lambda:e.verify(()),lambda:e.verify([StateEigen(q)]),lambda:e.verify((StateEigen((4,0,0)),)),lambda:e.verify((Transition(p,q),StateEigen((0,0,True)))),lambda:e.verify((StateEigen(q),),max_work=True),lambda:Engine(s,Policy(state_nodes=0)),lambda:Engine(s,Policy(prepare_state=1))):
        reject(f);checks+=1
    r=e.verify((StateEigen(q),)).reports[0]
    for changed in (replace(r,snapshot="0"*64),replace(r,obligation="0"*64),replace(r,domain="all-input-transition"),replace(r,expectation=((0,0),0))):
        assert replay_report(s,StateEigen(q),changed) is False;checks+=1
    assert replay_report(s,StateEigen(q),r,max_work=1) is None
    assert Engine(s,Policy(prepare_state=True,state_nodes=1)).verify((StateEigen(q),)).reports[0].status=="INCONCLUSIVE"
    return {"checks":checks+2,"scope":"domain separation, immutable input preflight, tampered reports and budget exhaustion"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"integrated":integrated,"workloads":workloads,"admission":admission}[sys.argv[1]]()},indent=2,allow_nan=False))
