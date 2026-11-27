"""G: externally sampled live RSS, baseline after startup and preparation."""
import sys,subprocess,time,os,json
from common5 import *
from benchmark_engine import setup,routes
from test_engine import native
from engine import Native

def worker(n,g,m,route):
    c,p,obs=setup(n,g,m);backend=Native();fs=routes(c,p,obs,backend)
    print("READY",flush=True);assert sys.stdin.readline().strip()=="GO"
    for _ in range(8):
        rs=fs[route]();assert len(rs)==m
    print("DONE",flush=True);sys.stdin.readline()

def rss(pid):
    with open(f"/proc/{pid}/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):return int(line.split()[1])
    raise RuntimeError("RSS unavailable")

def main():
    import selectors
    native();rows=[]
    for n,g,m in ((16,1000,8),(32,10000,64)):
        for route in ("python_prepared","native_prepared","native_full","qiskit_prepared","qiskit_full"):
            p=subprocess.Popen([sys.executable,__file__,"--worker",str(n),str(g),str(m),route],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
            try:
                assert p.stdout.readline().strip()=="READY"
                baseline=rss(p.pid);samples=[baseline];p.stdin.write("GO\n");p.stdin.flush()
                sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
                while True:
                    samples.append(rss(p.pid))
                    if sel.select(timeout=.002):
                        assert p.stdout.readline().strip()=="DONE";break
                p.stdin.write("END\n");p.stdin.flush();assert p.wait(timeout=10)==0
                rows.append({"n":n,"gates":g,"m":m,"route":route,"baseline_kib":baseline,"sampled_max_kib":max(samples),"sampled_delta_kib":max(samples)-baseline,"sample_count":len(samples)})
            finally:
                if p.poll() is None:p.kill();p.wait()
    output({"scope":"Linux /proc sampled RSS at approx 2ms, eight repeated operations; can miss transient allocations, not high-water or controlled host; startup excluded by handshake, allocator retention persists","rows":rows})
if __name__=="__main__":
    if len(sys.argv)>1:worker(*map(int,sys.argv[2:5]),sys.argv[5])
    else:main()
