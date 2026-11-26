"""Isolated Linux process-tree RSS sampling for remaining performance decisions.

Sampled simultaneous RSS sums double-count shared pages; not exact physical
memory or a strict peak bound. Workers retain outputs until acknowledgement.
"""
import argparse,json,multiprocessing,os,select,subprocess,sys,time
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from pathlib import Path
import numpy as np
from research.expressive_composition_cost import workload as composition_fixture,_one_staged_copy
from research.composition_suffix_transaction import suffix_transaction
from research.explicit_sweep_parallelism import workload as sweep_fixture,thread_task,process_task

def read_rss(pid):
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):return int(line.split()[1])
    except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    return 0

def process_tree(pid):
    seen=set();todo=[pid]
    while todo:
        p=todo.pop()
        if p in seen:continue
        seen.add(p)
        try:
            tasks=list(Path(f"/proc/{p}/task").iterdir())
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue
        for task in tasks:
            try:todo.extend(int(x) for x in (task/"children").read_text().split())
            except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    return seen

def sample(pid):
    values={p:read_rss(p) for p in process_tree(pid)}
    return dict(parent_kib=values.get(pid,0),children_kib=sum(v for p,v in values.items() if p!=pid),
                total_kib=sum(values.values()),processes=sum(v>0 for v in values.values()))

def own_memory():
    values={}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:","VmHWM:")):
            key,value=line.split(":",1);values[key]=int(value.split()[0])
    return values

def worker(kind,variant):
    if kind=="composition":
        c,u,v,cw,aw=composition_fixture(10000)
        expected=c.to_qiskit()
        un,vn=u.to_qiskit(),v.to_qiskit()
        for block,wires in ((un,cw),(vn,aw),(un.inverse(),cw)):
            expected.compose(block,qubits=list(wires),inplace=True)
        if variant=="current":run=lambda:c.compute_action_uncompute(u,v,compute_wires=cw,action_wires=aw)
        elif variant=="staged":run=lambda:_one_staged_copy(c,u,v,cw,aw)
        elif variant=="suffix":run=lambda:suffix_transaction(c,u,v,cw,aw)
        else:raise ValueError("unknown variant")
        pool=None
    elif kind=="sweep":
        cs,payloads,expected=sweep_fixture(14,16)
        pool=None
        if variant=="serial":run=lambda:tuple(map(thread_task,cs))
        elif variant=="threads":
            pool=ThreadPoolExecutor(max_workers=2)
            run=lambda:tuple(pool.map(thread_task,cs))
        elif variant=="processes":
            pool=ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context("spawn"))
            run=lambda:tuple(pool.map(process_task,payloads))
        else:raise ValueError("unknown variant")
    else:raise ValueError("unknown workload")
    try:
        print(json.dumps({"event":"ready","own":own_memory()}),flush=True)
        if sys.stdin.readline().strip()!="start":raise RuntimeError("missing start")
        start=time.perf_counter_ns()
        out=run()
        first=(time.perf_counter_ns()-start)/1e6
        # Same process, second warm sweep; composition is a one-shot mutation.
        warm=None
        if kind=="sweep":
            del out
            start=time.perf_counter_ns();out=run()
            warm=(time.perf_counter_ns()-start)/1e6
        print(json.dumps({"event":"done","own":own_memory(),"first_ms":first,"second_ms":warm}),flush=True)
        if sys.stdin.readline().strip()!="verify":raise RuntimeError("missing verification")
        if kind=="composition":
            assert out.to_qiskit()==expected and out.checkpoints=={}
            assert u.to_qiskit()==un and v.to_qiskit()==vn
        else:
            np.testing.assert_allclose(out,expected,atol=1e-9,rtol=0)
            assert tuple(x.to_json() for x in cs)==payloads
        print(json.dumps({"event":"verified"}),flush=True)
    finally:
        if pool is not None:pool.shutdown(wait=True)

def line_with_timeout(stream,timeout):
    ready,_,_=select.select([stream],[],[],timeout)
    if not ready:raise TimeoutError("worker protocol timeout")
    line=stream.readline()
    if not line:raise RuntimeError("worker exited before protocol completion")
    return json.loads(line)

def measure(kind,variant):
    if not sys.platform.startswith("linux"):raise RuntimeError("Linux /proc required")
    cmd=[sys.executable,"-m","research.performance_memory_closure","--worker",kind,"--variant",variant]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1) as p:
        try:
            ready=line_with_timeout(p.stdout,90)
            assert ready["event"]=="ready"
            before=sample(p.pid)
            samples=[dict(elapsed_ms=0.,**before)]
            start=time.monotonic()
            p.stdin.write("start\n");p.stdin.flush()
            while True:
                samples.append(dict(elapsed_ms=(time.monotonic()-start)*1000,**sample(p.pid)))
                readable,_,_=select.select([p.stdout],[],[],.005)
                if readable:break
                if time.monotonic()-start>90:raise TimeoutError("workload timeout")
            done=line_with_timeout(p.stdout,1);assert done["event"]=="done"
            samples.append(dict(elapsed_ms=(time.monotonic()-start)*1000,**sample(p.pid)))
            p.stdin.write("verify\n");p.stdin.flush()
            assert line_with_timeout(p.stdout,90)["event"]=="verified"
            assert p.wait(timeout=90)==0
            return dict(kind=kind,variant=variant,before=before,own_before=ready["own"],own_after=done["own"],
                        first_ms=done["first_ms"],second_ms=done["second_ms"],
                        sampled_peak_total_kib=max(s["total_kib"] for s in samples),
                        sampled_peak_children_kib=max(s["children_kib"] for s in samples),
                        samples=samples,verified=True)
        finally:
            if p.poll() is None:p.kill();p.wait()

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path)
    p.add_argument("--worker",choices=("composition","sweep"));p.add_argument("--variant")
    p.add_argument("--repetitions",type=int,default=3)
    a=p.parse_args()
    if a.worker:worker(a.worker,a.variant);return
    if not a.output or not 1<=a.repetitions<=5:p.error("output and 1..5 repetitions required")
    rows=[]
    for rep in range(a.repetitions):
        for kind,variants in (("composition",("current","staged","suffix")),("sweep",("serial","threads","processes"))):
            for variant in (variants if rep%2==0 else reversed(variants)):
                row=dict(rep=rep,**measure(kind,variant));rows.append(row)
                print(json.dumps({k:v for k,v in row.items() if k!="samples"},allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="Linux /proc sampled simultaneous RSS, shared pages double counted, short peaks may be missed; own HWM includes preparation",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
