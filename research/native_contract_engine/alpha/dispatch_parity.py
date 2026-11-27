"""A4 installed candidate: compare complete reports to A3 dispatch semantics.

The reference explicitly retains the previous layered path for pure
transition batches. This is not an independent mathematical oracle;
Qiskit parity and prior independent replay remain separate requirements.
"""
import json,random,statistics,time
from dataclasses import replace
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford,PauliList
from qcontract import Contract,StateEigen,prepare
from qcontract._core.qualified30 import Report,validate as validate_base
from qcontract._core.qualified31 import validate as validate_outer
from qcontract._core.consolidated12 import Engine as Legacy

def reference(p,specs,budget):
    core=p._engine.base.prepared;s=core.session;n=s.width
    # Reconstruct the A3 pure-transition route, including the two
    # admission passes and old safe batch threshold.
    outer=tuple(validate_outer(s,x) for x in specs)
    q=budget//len(specs)
    if not q:return tuple(Report("INCONCLUSIVE",d,ids,oid,0) for d,ids,oid in outer)
    _legacy=Legacy(s)
    keys=tuple(validate_base(s,x) for x in specs)
    if len(specs)>1 and core.router.previous.prepared.tableau is not None and q>=6*n+7:
        details=core.verify(specs,max_work=q*len(specs)).reports
    else:details=tuple(core.verify((x,),max_work=q).reports[0] for x in specs)
    return tuple(Report(r.status,d,ids,oid,q,r) for (d,ids,oid),r in zip(keys,details))

def label(n,p):
    x,z,sign=p
    return ("-" if sign else "")+"".join("IZXY"[2*((x>>i)&1)+((z>>i)&1)] for i in reversed(range(n)))
def mask(p):
    return (sum(int(v)<<i for i,v in enumerate(p.x)),sum(int(v)<<i for i,v in enumerate(p.z)),int(p.phase)//2)
def time_routes(routes,reps=17):
    rng=random.Random(4402);data={name:[] for name in routes}
    for fn in routes.values():fn();fn()
    for _ in range(reps):
        order=list(routes);rng.shuffle(order)
        for name in order:
            start=time.perf_counter_ns();routes[name]();data[name].append((time.perf_counter_ns()-start)/1e6)
    return {k:{"median_ms":statistics.median(v),"samples_ms":v} for k,v in data.items()}

def main():
    rng=random.Random(4401);checks=0;rows=[]
    for n in (1,2,3,4,7,8,15,16,31,32,63,64):
        c=QuantumCircuit(n)
        for _ in range(256):
            a=rng.randrange(n)
            if n>1 and rng.randrange(3)==0:
                b=rng.randrange(n-1);b+=b>=a;c.cx(a,b)
            else:getattr(c,rng.choice(("h","s","sdg","x","z")))(a)
        p=prepare(c);cl=Clifford(c)
        ps=tuple((0,0,0) if j%4==0 else ((1<<n)-1,(1<<n)-1,j%2) if j%4==1 else (rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for j in range(64))
        actual=tuple(mask(v) for v in PauliList([label(n,x) for x in ps]).evolve(cl,frame="h"))
        specs=tuple(Contract(requires=(a[0],a[1],a[2]^(j%2)),ensures=b) for j,(a,b) in enumerate(zip(actual,ps)))
        for count in (1,2,7,64):
            selected=specs[:count]
            for q in sorted({0,1,4*n+6,4*n+7,4*n+8,6*n+6,6*n+7,6*n+8,2_000_000//count}):
                budget=max(1,q*count)
                got=tuple(r._raw for r in p.verify(*selected,max_work=budget))
                want=reference(p,selected,budget)
                assert got==want,(n,count,budget)
                checks+=count
            got=p.verify(*selected)
            assert all(r.status==("PASS" if j%2==0 else "FAIL") for j,r in enumerate(got))
            checks+=count
        # A mixed request is still routed through the existing facade.
        mixed=(specs[0],StateEigen((0,0,0)),specs[1])
        for budget in (1,3,3*(6*n+7),2_000_000):
            got=p.verify(*mixed,max_work=budget);q=budget//len(mixed)
            if q:assert all(r==p.check(x,max_work=q) for r,x in zip(got,mixed))
            else:assert all(r.status=="INCONCLUSIVE" for r in got)
            checks+=len(mixed)
        try:p.verify(specs[0],Contract(requires=(True,0,0),ensures=ps[0]))
        except (TypeError,ValueError):checks+=1
        else:raise AssertionError("invalid batch accepted")
        for count in (1,64):
            selected=specs[:count];budget=2_000_000
            routes={"direct":lambda:p._engine.verify(selected,max_work=budget),
                    "a3_reference":lambda:reference(p,selected,budget)}
            rows.append({"width":n,"queries":count,"timings":time_routes(routes)})
    # Non-Clifford and disabled preparation must retain existing fallback.
    for mode in ("nonclifford","no_tableau"):
        c=QuantumCircuit(2);c.h(0)
        if mode=="nonclifford":c.t(0)
        p=prepare(c,tableau_build_work=1 if mode=="no_tableau" else 2_000_000)
        specs=(Contract(requires=(0,0,0),ensures=(0,0,0)),Contract(requires=(0,0,1),ensures=(0,0,0)))
        for budget in (1,2,100,2_000_000):
            assert tuple(r._raw for r in p.verify(*specs,max_work=budget))==reference(p,specs,budget)
            checks+=len(specs)
    print(json.dumps({"checks":checks,"rows":rows,"scope":"complete R30 reports against reconstructed A3 dispatch, Qiskit signed-image oracle, per-item boundary and fallback parity; timings of internal report dispatch only"},indent=2,allow_nan=False))
if __name__=="__main__":main()
