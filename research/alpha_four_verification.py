"""#109 matched diagnostics, isolated workers, explicit evidence scopes."""
import argparse,json,os,random,resource,subprocess,sys,time
import numpy as np
import ketary as q
from qiskit.quantum_info import Pauli,Statevector
from research.circuit_rewrite_ladder import stats
from research.performance_memory_closure import sample

def grouped(n,route):
    c=q.Circuit(n).h(range(n))
    for i in range(n-1):c.cx(i,i+1)
    c.ry(.37,n-1)
    r=c.run();labels=["I"*(n-1)+a for a in "XYZ"]+["X"*n,"Z"*n]
    obs=[q.Observable({label:.7,"I"*n:.2}) for label in labels]
    obs=obs+obs
    ref=Statevector(r.math.statevector())
    want=tuple(.7*float(ref.expectation_value(Pauli(label)).real)+.2 for label in labels)*2
    fn=(lambda:r.math.expectations(obs)) if route=="grouped" else (lambda:tuple(r.math.expectation(o) for o in obs))
    def check(v):np.testing.assert_allclose(v,want,atol=1e-9,rtol=0)
    return fn,check,len(obs)*8

def checkpoint(n,route):
    c=q.Circuit(n).h(0).checkpoint("first")
    for i in range(n-1):c.cx(i,i+1)
    c.checkpoint("entangled").z(0).checkpoint("defect")
    contracts={"first":q.Contract(n,expectations={"I"*(n-1)+"X":1}),
               "entangled":q.Contract(n,expectations={"X"*n:1}),
               "defect":q.Contract(n,expectations={"X"*n:-1})}
    if route=="grouped":
        def fn():
            result=c.debug.verify_checkpoints(contracts)
            return tuple(row["report"]["status"] for row in result["checks"])
    else:
        def fn():return tuple(contract.verify(c.debug.checkpoint(name).result).status for name,contract in contracts.items())
    def check(v):assert v==("PASS","PASS","PASS")
    return fn,check,None

def replay(n,route):
    good=q.ghz(n);bad=good.copy().z(0)
    label="0"*n
    report=bad.test.compare(good,inputs=[label],complete=False,ignore_global_phase=False)
    assert report.status=="FAIL" and report.evidence is not None
    payload=report.evidence.to_json()
    def typed():
        result=q.Evidence.from_json(payload).reproduce()
        assert result["reproduced"]
        return result["state_l2"]
    def direct():
        data=json.loads(payload)["data"]
        a,b=q.Circuit.from_json(data["observed"]),q.Circuit.from_json(data["reference"])
        return float(np.linalg.norm(a.run(initial_state=data["input"]).math.statevector()-b.run(initial_state=data["input"]).math.statevector()))
    def check(v):np.testing.assert_allclose(v,np.sqrt(2),atol=1e-9,rtol=0)
    return (typed if route=="typed" else direct),check,len(payload.encode())

def external(n,route):
    a=q.ghz(n);b=a.copy().x(0).x(0)
    if route=="different":b.z(0)
    def fn():return a.test.external_equivalence(b,deadline=10).status
    def check(v):assert v==("PASS" if route=="equal" else "FAIL")
    return fn,check,None

def worker(family,n,route,reps):
    fn,check,payload={"grouped":grouped,"checkpoint":checkpoint,"replay":replay,"external":external}[family](n,route)
    baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({"event":"ready","baseline_hwm_kib":baseline}),flush=True)
    if sys.stdin.readline().strip()!="go":raise RuntimeError("missing start")
    times=[]
    for _ in range(reps):
        t=time.perf_counter_ns();out=fn();e=time.perf_counter_ns()
        check(out);times.append((e-t)/1e6)
    print(json.dumps(dict(event="done",family=family,n=n,route=route,timing=stats(times),payload_bytes=payload,baseline_hwm_kib=baseline,post_hwm_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
    if sys.stdin.readline().strip()!="exit":raise RuntimeError("missing acknowledgement")

def isolated(family,n,route,reps):
    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
    proc=subprocess.Popen([sys.executable,"-m","research.alpha_four_verification","--worker",family,str(n),route,"--reps",str(reps)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,env=env,bufsize=1)
    import select
    try:
        if not select.select([proc.stdout],[],[],120)[0]:raise TimeoutError("worker setup")
        ready=json.loads(proc.stdout.readline());assert ready["event"]=="ready"
        baseline=sample(proc.pid);peak=baseline.copy()
        proc.stdin.write("go\n");proc.stdin.flush()
        deadline=time.monotonic()+120
        while True:
            current=sample(proc.pid)
            for k in peak:peak[k]=max(peak[k],current[k])
            if select.select([proc.stdout],[],[],.01)[0]:break
            if time.monotonic()>deadline:raise TimeoutError("worker execution")
        row=json.loads(proc.stdout.readline());assert row["event"]=="done"
        current=sample(proc.pid)
        for k in peak:peak[k]=max(peak[k],current[k])
        proc.stdin.write("exit\n");proc.stdin.flush()
        assert proc.wait(timeout=15)==0
        row.update(baseline_tree=baseline,sampled_tree_max=peak)
        return row
    finally:
        if proc.poll() is None:proc.kill();proc.wait()

def study(reps,external_only=False):
    if not sys.platform.startswith("linux"):raise RuntimeError("Linux RSS units")
    families={"external":("equal","different")} if external_only else {"grouped":("grouped","scalar"),"checkpoint":("grouped","scalar"),"replay":("typed","direct")}
    rows=[];rng=random.Random(1101)
    for n in (4,8):
        for family,routes in families.items():
            for route in rng.sample(list(routes),len(routes)):
                rows.append(isolated(family,n,route,reps))
    return dict(scope="matched grouped values and checkpoint verdicts; typed replay includes schema/hash validation absent from direct replay; external QCEC separate relation; sampled simultaneous tree RSS sums shared pages and can miss transients, HWM is worker only; shared CI",rows=rows)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--worker",nargs=3);p.add_argument("--external",action="store_true");p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if not 1<=a.reps<=20:p.error("reps 1..20")
    if a.worker:worker(a.worker[0],int(a.worker[1]),a.worker[2],a.reps)
    else:print(json.dumps(study(a.reps,a.external),indent=2,allow_nan=False))
