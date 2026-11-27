"""Matched end-to-end research timings and Linux per-process high-water RSS.
No timing assertions. Every route returns the same scoped status/witness.
"""
import json, os, sys, random, statistics, time, subprocess, resource, platform
from dataclasses import asdict
import numpy as np
from qiskit.quantum_info import Clifford, Pauli
from benchmark import ROOT,label,random_g
from round3 import prepare
from engine import Obligation,verify,Native,Report,SCOPE,admission,digest,difference,product_witness
from test_engine import circuit,native

def bits(p):
    assert int(p.phase) in (0,2)
    return sum(int(x)<<i for i,x in enumerate(p.x)),sum(int(z)<<i for i,z in enumerate(p.z)),int(p.phase)//2

def reference(c,pre,obs,cl=None):
    cid=admission(pre)
    if cl is None:cl=Clifford(c.to_qiskit())
    reports=[]
    for ob in obs:
        x,z,r=bits(Pauli(label(pre.width,ob.post)).evolve(cl,frame="h"))
        d=difference(((x,z,(-1)**r,0),),0,ob.pre)
        reports.append(Report("FAIL" if d else "PASS","qiskit",cid,digest(asdict(ob)),SCOPE,
                     "nonzero exact product-state expectation" if d else "exact coefficient equality",
                     product_witness(pre.width,d,0) if d else None))
    return tuple(reports)

def setup(n,g,m):
    rng=random.Random(771+n+g+m)
    gs=[]
    for i in range(g):
        a,b=rng.sample(range(n),2);op=rng.randrange(6)
        gs.append((op,a,b if op==5 else 0))
    c=circuit(n,gs);p=prepare(c)
    cl=Clifford(c.to_qiskit())
    obs=[]
    for i in range(m):
        post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
        x,z,r=bits(Pauli(label(n,post)).evolve(cl,frame="h"))
        obs.append(Obligation((x,z,r^(i%2)),post))
    return c,p,tuple(obs)

def routes(c,p,obs,backend):
    cl=Clifford(c.to_qiskit())
    return {"python_prepared":lambda:verify(p,obs,method="python"),
            "native_prepared":lambda:verify(p,obs,native=backend),
            "native_full":lambda:verify(prepare(c),obs,native=backend),
            "qiskit_prepared":lambda:reference(c,p,obs,cl),
            "qiskit_full":lambda:reference(c,prepare(c),obs)}

def projection(rs):
    return [(r.status,r.circuit_id,r.obligation_id,r.witness) for r in rs]

def memory(n,g,m,route):
    # Fresh subprocess for every route. Setup uses a Clifford reference to
    # generate identical obligations, so startup peak may mask later deltas.
    c,p,obs=setup(n,g,m);backend=Native()
    baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    f=routes(c,p,obs,backend)[route]
    rs=f()
    assert [r.status for r in rs]==["FAIL" if i%2 else "PASS" for i in range(m)]
    high=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({"route":route,"n":n,"gates":g,"m":m,
                      "setup_highwater_kib":baseline,"process_highwater_kib":high,
                      "additional_highwater_kib":max(0,high-baseline)}))

def main():
    backend=native();rng=random.Random(4123);rows=[]
    for n in (16,32):
        for g in (100,10000):
            for m in (1,8,64):
                c,p,obs=setup(n,g,m);fs=routes(c,p,obs,backend)
                expected=projection(fs["qiskit_full"]())
                assert [x[0] for x in expected]==["FAIL" if i%2 else "PASS" for i in range(m)]
                for f in fs.values():
                    assert projection(f())==expected
                    for _ in range(2):f()
                raw={k:[] for k in fs}
                for _ in range(9):
                    keys=list(fs);rng.shuffle(keys)
                    for k in keys:
                        t=time.perf_counter_ns();fs[k]();raw[k].append((time.perf_counter_ns()-t)/1e6)
                rows.append({"n":n,"gates":g,"m":m,"timings":{k:{"median_ms":statistics.median(v),"p95_ms":float(np.percentile(v,95)),"samples_ms":v} for k,v in raw.items()}})
    mem=[]
    for n,g,m in ((16,100,1),(32,10000,64)):
        for route in ("python_prepared","native_prepared","native_full","qiskit_prepared","qiskit_full"):
            out=subprocess.check_output([sys.executable,__file__,"--memory",str(n),str(g),str(m),route],text=True)
            mem.append(json.loads(out))
    print(json.dumps({"python":platform.python_version(),"scope":"full exact Pauli transition reports, status/hash/witness parity, shared CI diagnostic; Linux ru_maxrss includes setup; additional high-water not allocation peak or RSS guarantee","repetitions":9,"rows":rows,"memory":mem},indent=2,allow_nan=False))

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--memory":memory(*map(int,sys.argv[2:5]),sys.argv[5])
    else:main()
