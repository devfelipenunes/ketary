"""R24 independent validation and component-level profiling."""
import json,random,sys,tracemalloc
from itertools import product
from common5 import measure
from native9 import RustSession
from engine import product_witness,difference
from prepared23 import Prepared
from unified24 import Unified,Compact
from certificate23 import verify_bytes
from planner19 import plan_transition
from dag22 import simulate
from expectation23 import expectation,eigen_contract

def pack(gs):return bytes(v for g in gs for v in g)
def gen(n,count,seed):
    rng=random.Random(seed);rows=[]
    for _ in range(count):
        a,b=rng.sample(range(n),2);op=rng.randrange(6);rows.append((op,a,b if op==5 else 0))
    return rows
def reject(fn):
    try:fn()
    except (ValueError,TypeError,OverflowError):return
    raise AssertionError("expected rejection")

def witnesses():
    checks=0;rng=random.Random(2401)
    s=RustSession(2,b"");p=Unified(s)
    paulis=tuple(product(range(4),range(4),(0,1)))
    for b in paulis:
        items=tuple((a,b) for a in paulis)
        ref=p.prepared.transitions(items);got=p.transitions(items)
        assert [(r.status,r.witness) for r in ref]==[(r.status,r.expanded().witness) for r in got]
        checks+=len(items)
    for n in (2,8,32,64):
        s=RustSession(n,pack(gen(n,512,n)));p=Unified(s)
        for j in range(8):
            items=[]
            for i in range(64):
                b=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));r=s.propagate(b);x,z,c,_=r.terms[0]
                a=(x,z,int(c<0)) if i%3==0 else (x,z,int(c>0)) if i%3==1 else (rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
                items.append((a,b))
            items=tuple(items);ref=p.prepared.transitions(items);got=p.transitions(items)
            assert [(r.status,r.witness) for r in ref]==[(r.status,r.expanded().witness) for r in got]
            assert all(r.circuit_id==s.identity for r in got)
            for budget in (1,2*(2*n+3)+1,1000):
                assert [r.status for r in p.transitions(items,max_work=budget)]==[r.status for r in p.prepared.transitions(items,max_work=budget)]
            checks+=len(items)+3
    reject(lambda:p.transitions((((0,0,0),(0,0,True)),)))
    return {"checks":checks+1,"scope":"compact native exact witness, legacy deterministic witness parity"}

def routing():
    rows=[];checks=0
    for n in (2,8,16,32,64):
        gs=[g for i in range(n) for g in [(6,i,0),(4,i,0),(7,i,0),(4,i,0)]]
        chain=[(5,i,i+1) for i in range(n-1)];gs+=chain+chain[::-1]
        if len(gs)%4:gs.extend([(4,0,0),(4,0,0)])
        s=RustSession(n,pack(gs));p=Unified(s);x=((1<<n)-1,0,0)
        got=p.transitions(((x,x),))[0];assert got.status=="PASS"
        if got.route=="temporal-certificate":assert verify_bytes(n,s.packed,x,x,got.certificate);checks+=1
        if n>=32:assert got.route=="temporal-certificate"
        bad=(x[0],0,1);r=p.transitions(((bad,x),))[0]
        assert r.status in ("FAIL","INCONCLUSIVE")
        assert p.transitions(((x,x),),max_work=1)[0].status=="INCONCLUSIVE"
        rows.append({"n":n,"gates":len(gs),"route":got.route,"baseline":plan_transition(s,x,x).status,"mutant":r.status})
        checks+=3
    return {"checks":checks,"rows":rows,"scope":"disjoint logical budgets, exact certificate fallback only for PASS"}

def profile():
    rows=[];rng=random.Random(2402)
    for n in (4,16,32,64):
        s=RustSession(n,pack(gen(n,4096,n)));p=Unified(s);t=p.prepared.tableau
        for fail_percent in (0,50,100):
            items=[]
            for i in range(32):
                b=(rng.getrandbits(n),rng.getrandbits(n),0);a=t.image(b)
                if i*100<fail_percent*32:a=(a[0],a[1],a[2]^1)
                items.append((a,b))
            items=tuple(items);posts=tuple(b for a,b in items);reports=p.transitions(items)
            assert sum(r.status=="FAIL" for r in reports)==(32*fail_percent)//100
            routes={"old_reports":lambda:p.prepared.transitions(items),
                    "images_only":lambda:t.images(posts,1,2_000_000),
                    "native_contracts":lambda:t.contracts(items,2_000_000),
                    "compact_reports":lambda:p.transitions(items),
                    "expanded_reports":lambda:tuple(r.expanded() for r in p.transitions(items)),
                    "expand_only":lambda:tuple(r.expanded() for r in reports)}
            timings=measure(routes,reps=21)
            peaks={}
            for name in ("old_reports","compact_reports","expanded_reports"):
                tracemalloc.start();routes[name]();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();peaks[name]=peak
            rows.append({"n":n,"failure_percent":fail_percent,"timings":timings,"python_peak_bytes":peaks,"native_retained_payload_bytes":t.storage_bytes()})
    return {"rows":rows,"scope":"component times overlap; tracemalloc is Python only; retained native payload excludes allocator overhead and temporary allocations"}

def wide():
    rows=[];checks=0
    for n in (30,40,50,64):
        mask=(1<<n)-1
        for name,gs,obs in (
            ("uniform",[(0,i,0) for i in range(n)],(mask,0,0)),
            ("ghz",[(0,0,0)]+[(5,0,i) for i in range(1,n)],(mask,0,0)),
            ("phase",[(0,i,0) for i in range(n)]+[(6,i,0) for i in range(n)],(0,0,0))):
            g=pack(gs);d=simulate(n,g,wide=True);assert d is not None
            assert eigen_contract(d,obs)=="PASS"
            assert eigen_contract(d,(obs[0],obs[1],1))=="FAIL"
            if name=="ghz":assert eigen_contract(d,(0,3,0))=="PASS" and eigen_contract(d,(0,1,0))=="FAIL";checks+=2
            if name=="phase":
                e=expectation(d,(1,0,0));assert e.numerator==(0,1) and e.denominator_power==1
                checks+=1
            rows.append({"n":n,"case":name,"active_nodes":d.live_nodes(),"arena_nodes":len(d.nodes),"visits":expectation(d,obs).visits,"timings":measure({"simulate":lambda:simulate(n,g,wide=True),"contract":lambda:eigen_contract(d,obs)},reps=9)})
            checks+=2
    assert simulate(64,b"",wide=True,cap=1) is None
    reject(lambda:simulate(64,b""))
    return {"checks":checks+2,"rows":rows,"scope":"structured exact unweighted DAG up to 64 wires, no dense expansion or arbitrary scalability claim"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"witnesses":witnesses,"routing":routing,"profile":profile,"wide":wide}[sys.argv[1]]()},indent=2,allow_nan=False))
