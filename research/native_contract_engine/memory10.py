"""Matched independent worker RSS and latency on Linux, no startup-peak claim."""
import sys,subprocess,selectors,time,resource,json
from common5 import *
from native9 import RustSession
from front_g import rss

def worker(route,t):
    n=64;c=circuit(n,[(4,i%n,0) for i in range(100)]+[(6,i,0) for i in range(t)])
    p=prepare(c,allow_t=True);s=RustSession.from_circuit(c);post=((1<<n)-1,0,0);obs=(Obligation(post,post),)
    fn=(lambda:verify(p,obs,method="sparse")) if route=="python" else (lambda:s.verify(obs))
    print("READY",flush=True);assert sys.stdin.readline().strip()=="GO"
    samples=[]
    for _ in range(7):
        start=time.perf_counter_ns();r=fn()[0];samples.append((time.perf_counter_ns()-start)/1e6)
        assert r.status=="FAIL" and r.witness is not None
    print(json.dumps({"times_ms":samples,"highwater_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True);sys.stdin.readline()
def main():
    rows=[]
    for t in (8,12):
        for trial in range(3):
            for route in ("python","rust"):
                p=subprocess.Popen([sys.executable,__file__,"worker",route,str(t)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
                try:
                    assert p.stdout.readline().strip()=="READY";baseline=rss(p.pid);samples=[baseline]
                    p.stdin.write("GO\n");p.stdin.flush()
                    with selectors.DefaultSelector() as sel:
                        sel.register(p.stdout,selectors.EVENT_READ)
                        while True:
                            samples.append(rss(p.pid))
                            if sel.select(timeout=.001):
                                result=json.loads(p.stdout.readline());break
                    p.stdin.write("END\n");p.stdin.flush();assert p.wait(timeout=10)==0
                    rows.append({"T":t,"trial":trial,"route":route,"baseline_kib":baseline,"sampled_max_kib":max(samples),"sampled_delta_kib":max(samples)-baseline,"samples":len(samples),**result})
                finally:
                    if p.poll() is None:p.kill();p.wait()
    output({"scope":"Linux live RSS sampled ~1ms, separate processes with identical setup, seven requests; may miss short-lived allocations; highwater includes setup; no dedicated host","rows":rows})
if __name__=="__main__":
    if len(sys.argv)>1:worker(sys.argv[2],int(sys.argv[3]))
    else:main()
