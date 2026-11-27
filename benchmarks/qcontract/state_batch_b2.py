"""B2 candidate: measure exact Clifford state batching and diagnose overhead.

Experimental, NOT part of the public Alpha. The validated engine and
independent Qiskit references are retained. Full report comparison uses
the current public API; the candidate returns only exact expectations.
"""
import json,random,time,statistics,cProfile,pstats,io
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford,PauliList
from qcontract import prepare,StateEigen,Contract

def label(n,p):
    x,z,s=p
    return ("-" if s else "")+"".join("IZXY"[2*((x>>i)&1)+((z>>i)&1)] for i in reversed(range(n)))

def image_batch(p,observables,*,max_work):
    """Prototype: zero-input expectation of inverse Clifford Pauli image.

    All inputs admitted first; equal per-item reservations; insufficient
    quota returns None, not zero. Logical work is not CPU or memory.
    """
    from qcontract._core.independent20 import pauli
    from qcontract._core.native9 import bounds
    bounds(4096,max_work)
    if type(observables) is not tuple or not 1<=len(observables)<=64:raise ValueError("bounded tuple")
    n=p.width
    for x in observables:pauli(n,x)
    table=p._engine.base.prepared.router.previous.prepared.tableau
    if table is None:return tuple(None for _ in observables)
    q=max_work//len(observables)
    indices=[i for i,(x,z,s) in enumerate(observables) if 3+x.bit_count()+z.bit_count()<=q]
    values=[None]*len(observables)
    if indices:
        raw=table.images(tuple(observables[i] for i in indices),1,q*len(indices))
        for i,(x,z,s) in zip(indices,raw):values[i]=((0 if x else (-1)**s,0),0)
    return tuple(values)

def time_routes(routes):
    samples={k:[] for k in routes};rng=random.Random(4702)
    for f in routes.values():f();f()
    for _ in range(13):
        order=list(routes);rng.shuffle(order)
        for k in order:
            start=time.perf_counter_ns();routes[k]();samples[k].append((time.perf_counter_ns()-start)/1e6)
    return {k:{"median_ms":statistics.median(v),"samples_ms":v} for k,v in samples.items()}

def main():
    rng=random.Random(4701);rows=[];checks=0
    for n in (2,4,8,16,32,64):
        for depth in (64,512):
            c=QuantumCircuit(n)
            for _ in range(depth):
                a,b=rng.sample(range(n),2);op=rng.randrange(6)
                if op==5:c.cx(a,b)
                else:getattr(c,("h","s","sdg","x","z")[op])(a)
            p=prepare(c);cl=Clifford(c).adjoint()
            ps=tuple((0,0,j%2) if j%4==0 else ((1<<n)-1,(1<<n)-1,j%2) if j%4==1 else (rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for j in range(64))
            for count in (1,8,32,64):
                obs=ps[:count];posts=PauliList([label(n,x) for x in obs]);specs=tuple(StateEigen(x) for x in obs)
                def oracle():
                    r=posts.evolve(cl,frame="s")
                    return tuple(((0 if any(x) else 1-2*(int(ph)//2),0),0) for x,ph in zip(r.x,r.phase))
                want=oracle()
                def candidate():return image_batch(p,obs,max_work=2_000_000)
                def public():return p.verify(*specs)
                got=candidate();assert got==want
                for spec,result,v in zip(specs,public(),want):
                    assert result.status in ("PASS","FAIL")
                    (a,b),k=result.expectation;assert (a,b)==(v[0][0]*(1<<k),0)
                    assert result.status==("PASS" if v[0][0]==1 else "FAIL")
                checks+=count
                for q in (0,1,2,3,4,2*n+2,2*n+3):
                    budget=max(1,q*count);quota=budget//count
                    expected=tuple(v if 3+x.bit_count()+z.bit_count()<=quota else None for (x,z,s),v in zip(obs,want))
                    assert image_batch(p,obs,max_work=budget)==expected;checks+=count
                rows.append({"width":n,"gates":depth,"queries":count,"timings":time_routes({"candidate_expectations":candidate,"public_full_reports":public,"qiskit_inverse_expectations":oracle})})
    # Profile actual public reports in a losing small-circuit batch, rather
    # than attributing time based on microbenchmarks alone.
    c=QuantumCircuit(2);c.h(0);c.cx(0,1);p=prepare(c)
    specs=tuple(Contract(requires=(0,0,j%2),ensures=(0,0,0)) for j in range(64))
    prof=cProfile.Profile();prof.enable()
    for _ in range(500):p.verify(*specs)
    prof.disable();out=io.StringIO();pstats.Stats(prof,stream=out).strip_dirs().sort_stats("cumulative").print_stats(35)
    c.t(0);assert image_batch(prepare(c),((0,0,0),),max_work=1000)==(None,);checks+=1
    try:image_batch(p,((True,0,0),),max_work=1000)
    except (ValueError,TypeError):checks+=1
    else:raise AssertionError("invalid mask accepted")
    print(json.dumps({"checks":checks,"rows":rows,"profile":out.getvalue(),"scope":"candidate exact expectation values vs same output Qiskit, full public reports separately; no public API change"},indent=2,allow_nan=False))
if __name__=="__main__":main()
