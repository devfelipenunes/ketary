"""Linux process resource qualification lab (not a production sandbox).

Each trusted fixed workload runs in a fresh process under OS address-space
and CPU limits, plus a parent wall-time limit. Peak RSS includes imports,
Python, Rust and runtime allocations. No arbitrary child command/input.
"""
import json,os,subprocess,sys,time

CASES=("native_clifford","native_sparse","dag_plain","dag_weighted","memory_cap","wall_cap","cpu_cap")

def worker(case):
    import resource
    memory=1024**3
    cpu=1 if case=="cpu_cap" else 12
    resource.setrlimit(resource.RLIMIT_AS,(memory,memory))
    resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu+1))
    if case=="memory_cap":
        try:bytearray(memory*2)
        except MemoryError:print(json.dumps({"status":"LIMIT","kind":"address-space"}));return
        raise AssertionError("address-space limit bypassed")
    if case=="wall_cap":time.sleep(30);raise AssertionError("wall timeout bypassed")
    if case=="cpu_cap":
        while True:pass
    from native9 import RustSession
    import ketary_native_research as rn
    from dag22 import simulate as plain
    from weighted27 import simulate as weighted
    n=32;g=bytes(x for i in range(n) for x in (0,i,0))
    start=time.perf_counter()
    if case=="native_clifford":
        s=RustSession(64,bytes((5,0,63))*4096);t=rn.CliffordTableau(s.native,2_000_000)
        r=t.contracts((((0,0,0),(0,0,0)),)*64,2_000_000);assert all(x and x[0] for x in r)
    elif case=="native_sparse":
        s=RustSession(16,bytes(x for i in range(8) for x in (6,i,0)))
        r=s.propagate((255,0,0));assert len(r.terms)==256
    else:
        g+=bytes(x for i in range(n) for x in (6,i,0))
        d=plain(n,g,wide=True) if case=="dag_plain" else weighted(n,g)
        assert d is not None
    print(json.dumps({"status":"PASS","case":case,"rss_peak_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"compute_ms":(time.perf_counter()-start)*1000,"address_space_bytes":memory,"cpu_soft_seconds":cpu}))

def run():
    import signal
    rows=[]
    for case in CASES:
        env=dict(os.environ,OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
        start=time.monotonic()
        try:
            p=subprocess.run([sys.executable,__file__,"worker",case],env=env,capture_output=True,text=True,timeout=.5 if case=="wall_cap" else 20)
        except subprocess.TimeoutExpired:
            assert case=="wall_cap";rows.append({"case":case,"status":"LIMIT","kind":"wall-time"});continue
        if case=="cpu_cap":
            assert p.returncode in (-signal.SIGXCPU,-signal.SIGKILL),p.stderr
            rows.append({"case":case,"status":"LIMIT","kind":"cpu-time","returncode":p.returncode});continue
        assert p.returncode==0,p.stderr
        r=json.loads(p.stdout)
        assert r["status"]==("LIMIT" if case=="memory_cap" else "PASS")
        rows.append({"case":case,**r,"wall_ms":(time.monotonic()-start)*1000})
    return {"checks":len(rows),"rows":rows,"scope":"Linux fixed child workloads; OS process limits and total process peak RSS, not per-call memory or portable sandbox"}

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="worker" and sys.argv[2] in CASES:worker(sys.argv[2])
    elif len(sys.argv)==1:print(json.dumps(run(),indent=2))
    else:raise SystemExit("invalid arguments")
