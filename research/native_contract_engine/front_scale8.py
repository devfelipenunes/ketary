"""Scale and explicit parallelism: 100k gates, repeated batch, matched reports."""
from common5 import *
from front_f7 import compact,run,project
from front_b import Session
from benchmark_engine import setup
from test_engine import native
from concurrent.futures import ThreadPoolExecutor
import os
def main():
    backend=native();rows=[];checks=0
    for n in (32,64):
        for count in (10000,100000):
            c,p,base=setup(n,count,8);s=Session(p);cp=compact(c)
            for m in (1,8):
                obs=base[:m]
                assert project(s.run(obs,native=backend))==project(run(cp,obs,backend));checks+=m
                fs={"legacy_cold":lambda:Session(prepare(c)).run(obs,native=backend),"compact_cold":lambda:run(compact(c),obs,backend),"compact_warm":lambda:run(cp,obs,backend)}
                rows.append({"n":n,"gates":count,"m":m,"timings":measure(fs,reps=9)})
    # Explicit caller-owned pools; each native invocation has independent
    # buffers; throughput comparison includes Python report construction.
    c,p,obs=setup(64,10000,64);cp=compact(c)
    seq=lambda:[run(cp,obs,backend) for _ in range(8)]
    expected=[project(r) for r in seq()]
    thread=[]
    for workers in (1,2,4):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            def parallel():return list(pool.map(lambda _:run(cp,obs,backend),range(8)))
            assert [project(r) for r in parallel()]==expected
            thread.append({"workers":workers,"timings":measure({"serial":seq,"explicit_pool":parallel},reps=9)})
    output({"scope":"100k gates research cap; shared Linux CI, explicit threads not runtime guarantee, bit-slicing already word parallel, no implicit threads","checks":checks,"rows":rows,"thread_rows":thread,"cpu_count":os.cpu_count(),"affinity":len(os.sched_getaffinity(0))})
if __name__=="__main__":main()
