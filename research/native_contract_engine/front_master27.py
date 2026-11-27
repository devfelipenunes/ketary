"""R27 weighted gate execution, portable spatial replay and integrated routing."""
import hashlib,json,random,sys
from common5 import measure
from native9 import RustSession
from independent20 import column,admit
from dag22 import simulate as plain
from weighted25 import amplitude,expectation
from expectation23 import expectation as plain_exp
from weighted27 import simulate
from spatial_evidence27 import produce,replay,canonical
from router27 import Router
from unified24 import Unified

def pack(gs):return bytes(v for g in gs for v in g)
def connected(n):
    gs=[g for i in range(n) for g in [(6,i,0),(4,i,0),(7,i,0),(4,i,0)]]
    chain=[(5,i,i+1) for i in range(n-1)]
    return pack(gs+chain+chain[::-1])
def weighted():
    rng=random.Random(2701);checks=0;rows=[]
    for n in (2,3,4,5):
        for j in range(24):
            gs=[]
            for _ in range(24):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            g=pack(gs);w=simulate(n,g);assert w is not None
            v,k=column(n,admit(n,g,2_000_000),0)
            assert w.denominator==k
            for i in range(1<<n):assert amplitude(w,i)==(v[i],k);checks+=1
            d=plain(n,g);assert d
            for _ in range(12):
                p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
                a,b=expectation(w,p),plain_exp(d,p)
                assert (a.status,a.numerator,a.denominator_power)==(b.status,b.numerator,b.denominator_power);checks+=1
    for n in (16,32,64):
        for name,gs in (("uniform",[(0,i,0) for i in range(n)]),("ghz",[(0,0,0)]+[(5,0,i) for i in range(1,n)]),("phase",[(0,i,0) for i in range(n)]+[(6,i,0) for i in range(n)])):
            g=pack(gs);w=simulate(n,g);d=plain(n,g,wide=True);assert w and d
            for p in ((1,0,0),((1<<n)-1,0,0),(0,3,0),(0,0,0)):
                a,b=expectation(w,p),plain_exp(d,p)
                assert (a.numerator,a.denominator_power)==(b.numerator,b.denominator_power);checks+=1
            rows.append({"n":n,"case":name,"weighted_nodes":len(w.nodes),"unweighted_nodes":d.live_nodes(),"timings":measure({"weighted":lambda:simulate(n,g),"unweighted":lambda:plain(n,g,wide=True)},reps=9)})
    assert simulate(2,b"",max_nodes=1) is None
    assert simulate(2,b"",max_work=1) is None
    return {"checks":checks+2,"rows":rows,"scope":"direct exact quarter-turn weighted gates, no general complex edge weights"}

def evidence():
    checks=0;rows=[]
    for n in (2,16,32,64):
        g=connected(n);p=((1<<n)-1,0,0);part=tuple((i,) for i in range(n))
        for a in (p,(p[0],0,1)):
            r=produce(n,g,a,p,part);assert r.status==("PASS" if a==p else "FAIL")
            raw=r.record;got=replay(n,g,a,p,raw);assert got and got.status==r.status and got.witness==r.witness
            for key,value in (("status","FAIL" if r.status=="PASS" else "PASS"),("result","0"*64),("partition",[[0]])):
                obj=json.loads(raw);obj["body"][key]=value
                obj["sha256"]=hashlib.sha256(canonical(obj["body"])).hexdigest()
                assert replay(n,g,a,p,canonical(obj)) is None;checks+=1
            assert replay(n,g+b"\x04\x00\x00",a,p,raw) is None
            assert replay(n,g,(a[0],a[1],a[2]^1),p,raw) is None
            assert replay(n,g,a,p,raw,max_work=1) is None
            assert replay(n,g,a,p,raw+b" ") is None
            rows.append({"n":n,"status":r.status,"bytes":len(raw),"logical_work":r.ledger.used,"timings":measure({"produce":lambda:produce(n,g,a,p,part),"replay":lambda:replay(n,g,a,p,raw)},reps=7)})
            checks+=6
    return {"checks":checks,"rows":rows,"scope":"independent-of-Rust replay recipe, recomputes exact transfer polynomial; no succinct proof or authentication"}

def routing():
    checks=0;rows=[]
    for n in (16,32,64):
        g=connected(n);s=RustSession(n,g);r=Router(s);p=((1<<n)-1,0,0);bad=(p[0],0,1)
        items=((p,p),(bad,p))
        out=r.transitions(items)
        assert [d.report.status for d in out]==["PASS","FAIL"]
        assert sum(d.reserved for d in out)<=2_000_000
        if n>=32:
            assert out[1].report.route=="spatial"
            assert replay(n,g,bad,p,out[1].report.certificate).status=="FAIL"
        assert all(d.report.status=="INCONCLUSIVE" for d in r.transitions(items,max_work=1))
        rows.append({"n":n,"routes":[d.report.route for d in out],"attempts":[[a.__dict__ for a in d.attempts] for d in out],"timings":measure({"router":lambda:r.transitions(items)},reps=7)})
        checks+=4
    s=RustSession(2,b"");r=Router(s);p=(1,0,0);items=((p,p),((1,0,1),p))
    got=r.transitions(items);ref=Unified(s).transitions(items)
    assert [d.report for d in got]==list(ref)
    assert all(d.shared_batch_budget==2_000_000 and d.reserved==0 for d in got)
    return {"checks":checks+2,"rows":rows,"scope":"private router; spatial fallback, per-item reservations and shared tableau budget separated"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"weighted":weighted,"evidence":evidence,"routing":routing}[sys.argv[1]]()},indent=2,allow_nan=False))
