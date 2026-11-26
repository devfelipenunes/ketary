"""Explicit warm-pool research; no SDK worker lifecycle or hidden concurrency."""
import argparse,json,multiprocessing,random,statistics,time
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
from pathlib import Path
import numpy as np
from research.explicit_sweep_parallelism import workload,thread_task,process_task

def evaluate(n,count,reps):
    if n not in (10,14) or count not in (4,16) or not 3<=reps<=20:
        raise ValueError("unsupported workload")
    cs,payloads,wanted=workload(n,count)
    samples={k:[] for k in ("serial","warm_threads","warm_processes")}
    orders=[];rng=random.Random(n+count)
    t=time.perf_counter_ns()
    with ThreadPoolExecutor(max_workers=2) as threads, ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context("spawn")) as processes:
        # Start each pool and validate the full ordered results before measurement.
        np.testing.assert_allclose(tuple(threads.map(thread_task,cs)),wanted,atol=1e-9,rtol=0)
        thread_ready=(time.perf_counter_ns()-t)/1e6
        start=time.perf_counter_ns()
        np.testing.assert_allclose(tuple(processes.map(process_task,payloads)),wanted,atol=1e-9,rtol=0)
        process_first=(time.perf_counter_ns()-start)/1e6
        routes={"serial":lambda:tuple(map(thread_task,cs)),
                "warm_threads":lambda:tuple(threads.map(thread_task,cs)),
                "warm_processes":lambda:tuple(processes.map(process_task,payloads))}
        for _ in range(reps):
            order=list(routes);rng.shuffle(order);orders.append(order)
            for name in order:
                start=time.perf_counter_ns();got=routes[name]();elapsed=(time.perf_counter_ns()-start)/1e6
                samples[name].append(elapsed)
                np.testing.assert_allclose(got,wanted,atol=1e-9,rtol=0)
                del got
        start=time.perf_counter_ns()
    teardown=(time.perf_counter_ns()-start)/1e6
    assert tuple(c.to_json() for c in cs)==payloads
    return dict(n=n,count=count,orders=orders,thread_first_and_pool_setup_ms=thread_ready,
                process_first_ms=process_first,teardown_ms=teardown,retained_output_bytes=count*16*(1<<n),
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=10)
    a=p.parse_args();rows=[]
    for n in (10,14):
        for count in (4,16):
            row=evaluate(n,count,a.repetitions);rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="explicit research pools; warm task timing excludes recorded startup/teardown; process replay and transport included; shared runner",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
