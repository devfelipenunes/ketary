"""End-to-end installed API benchmarks, not kernel-only microbenchmarks."""
import json,random,statistics,time
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford,PauliList
from qcontract import Contract,prepare

def timed(routes,reps=11):
    rng=random.Random(3303);samples={k:[] for k in routes}
    for f in routes.values():f();f()
    for _ in range(reps):
        keys=list(routes);rng.shuffle(keys)
        for k in keys:
            t=time.perf_counter_ns();routes[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
    return {k:{"median_ms":statistics.median(v),"p95_ms":float(np.percentile(v,95)),"samples_ms":v} for k,v in samples.items()}
def label(n,p):
    x,z,s=p
    return ("-" if s else "")+"".join("IZXY"[2*((x>>i)&1)+((z>>i)&1)] for i in reversed(range(n)))
def masks(p):
    return (sum(int(v)<<i for i,v in enumerate(p.x)),sum(int(v)<<i for i,v in enumerate(p.z)),int(p.phase)//2)
def main():
    rng=random.Random(3301);rows=[];checks=0
    for n in (4,16,32,64):
        for gates in (256,4096):
            c=QuantumCircuit(n)
            for _ in range(gates):
                a,b=rng.sample(range(n),2);op=rng.randrange(6)
                if op==5:c.cx(a,b)
                else:getattr(c,("h","s","sdg","x","z")[op])(a)
            p=prepare(c);cl=Clifford(c)
            setup=timed({"qcontract_prepare":lambda:prepare(c),"qiskit_clifford":lambda:Clifford(c)},7)
            for density in ("sparse","dense"):
                for count in (1,64):
                    ps=tuple(((1<<rng.randrange(n),1<<rng.randrange(n),rng.randrange(2)) if density=="sparse" else (rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))) for _ in range(count))
                    posts=PauliList([label(n,a) for a in ps])
                    expected=tuple(masks(a) for a in posts.evolve(cl,frame="h"))
                    targets=tuple((a[0],a[1],a[2]^(j%2)) for j,a in enumerate(expected))
                    pres=PauliList([label(n,a) for a in targets])
                    specs=tuple(Contract(requires=a,ensures=b) for a,b in zip(targets,ps))
                    want=tuple(j%2==0 for j in range(count))
                    def qiskit_verdicts(cliff):
                        got=posts.evolve(cliff,frame="h")
                        return tuple(bool(x) for x in (np.all(got.x==pres.x,axis=1)&np.all(got.z==pres.z,axis=1)&(got.phase==pres.phase)))
                    def reports():return p.verify(*specs)
                    def verdicts():return tuple(r.passed for r in reports())
                    assert verdicts()==qiskit_verdicts(cl)==want
                    assert all(r.status in ("PASS","FAIL") for r in reports())
                    assert all(r.witness is not None for r in reports() if r.status=="FAIL")
                    checks+=count
                    times=timed({"qcontract_reports":reports,"qcontract_verdicts":verdicts,"qiskit_verdicts":lambda:qiskit_verdicts(cl),
                                 "qcontract_end_to_end":lambda:tuple(r.passed for r in prepare(c).verify(*specs)),
                                 "qiskit_end_to_end":lambda:qiskit_verdicts(Clifford(c))},7)
                    rows.append({"width":n,"gates":gates,"density":density,"queries":count,"setup":setup,"timings":times})
    print(json.dumps({"checks":checks,"rows":rows,"scope":"installed public API vs vectorized Qiskit signed Clifford identity; matched verdicts but QContract computes additional witness/report data; prepared and end-to-end; shared CI"},indent=2,allow_nan=False))
if __name__=="__main__":main()
