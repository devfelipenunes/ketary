"""E: stage-level profiling and repeated verification throughput."""
from common5 import *
from engine import product_witness,admission,digest,verify
from front_b import Session
from front_b7 import grouped
from benchmark_engine import setup
from test_engine import native
from dataclasses import asdict
def main():
    backend=native();rows=[]
    for n,g,m in ((16,100,1),(32,10000,1),(32,10000,64),(64,10000,64)):
        c,p,obs=setup(n,g,m);s=Session(p);ps=[o.post for o in obs]
        old=lambda:s.run(obs,native=backend)
        new=lambda:grouped(s,obs,backend)
        assert semantic(old())==semantic(new())
        # Individual stages are distinct measurements, not additive decomposition.
        diff={(obs[0].pre[0],obs[0].pre[1]):(2,0)}
        routes={"prepare":lambda:prepare(c),"admission":lambda:admission(p),
                "native_propagation":lambda:backend.run(p,ps,"batch" if m>=8 else "scalar"),
                "obligation_hashes":lambda:[digest(asdict(o)) for o in obs],
                "example_witness":lambda:product_witness(n,diff,0),
                "session_report":old,"grouped_report":new,"cold_full":lambda:Session(prepare(c)).run(obs,native=backend)}
        rows.append({"n":n,"gates":g,"m":m,"timings":measure(routes,reps=11)})
    output({"scope":"isolated stage medians not additive; full cold vs warm and same report parity; shared CI, no timing thresholds","rows":rows})
if __name__=="__main__":main()
