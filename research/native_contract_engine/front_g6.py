"""Research: matched live RSS for repeated sessions without eager Clifford setup."""
import os,sys,subprocess,selectors,json
from common5 import *
from front_b import Session
from front_b6 import BoundNative
from front_g import rss
from test_engine import native
from engine import Native
def worker(route):
    # Build identical fixture without a tableau or baseline verifier.
    n=32;g=10000;m=64;p=prepare(circuit(n,gates(n,g)))
    rng=random.Random(77)
    obs=tuple(Obligation((rng.getrandbits(n),rng.getrandbits(n),0),(rng.getrandbits(n),rng.getrandbits(n),0)) for _ in range(m))
    session=Session(p);base=Native();bound=BoundNative(p)
    print("READY",flush=True);assert sys.stdin.readline().strip()=="GO"
    for _ in range(40):
        rs=session.run(obs,native=bound if route=="bound" else base);assert len(rs)==m
    print("DONE",flush=True);sys.stdin.readline()
def main():
    native();rows=[]
    for route in ("copy","bound"):
        for trial in range(3):
            p=subprocess.Popen([sys.executable,__file__,"worker",route],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
            try:
                assert p.stdout.readline().strip()=="READY";baseline=rss(p.pid);values=[baseline]
                p.stdin.write("GO\n");p.stdin.flush()
                with selectors.DefaultSelector() as sel:
                    sel.register(p.stdout,selectors.EVENT_READ)
                    while True:
                        values.append(rss(p.pid))
                        if sel.select(timeout=.001):
                            assert p.stdout.readline().strip()=="DONE";break
                p.stdin.write("END\n");p.stdin.flush();assert p.wait(timeout=10)==0
                rows.append({"route":route,"trial":trial,"baseline_kib":baseline,"max_kib":max(values),"delta_kib":max(values)-baseline,"samples":len(values)})
            finally:
                if p.poll() is None:p.kill();p.wait()
    output({"scope":"six isolated Linux subprocesses; same fixture/allocations before handshake, 40 requests, ~1ms RSS samples; may miss transient peaks","rows":rows})
if __name__=="__main__":
    if len(sys.argv)>1:worker(sys.argv[2])
    else:main()
