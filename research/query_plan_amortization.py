"""Paired amortized cost of the installed QueryPlan and the previous JSON route.

The legacy route emulates the old constructor/run from before #323, not an
installed previous wheel. Both export exactly the same evidence and estimates.
Process RSS is separate; no speed threshold on shared CI.
"""
import argparse,json,random,statistics,time
from pathlib import Path
import numpy as np
import ketary as q
from research.query_plan_cost import compare_nested,evidence,timed,stats

class Previous:
    def __init__(self,c,bits,paulis,subsystems):
        self._circuit=c.to_json()
        self.bits=tuple(bits);self.paulis=tuple(paulis);self.subsystems=tuple(subsystems)
    def estimate(self):
        d=json.loads(self._circuit);n=d["num_qubits"]
        return dict(state_payload_bytes=16*(1<<n),
                    density_output_bytes=sum(16*(1<<(2*len(w))) for w in self.subsystems),
                    gate_count=len(d["operations"]),simulation_count=1,
                    scope="payload estimates; not total memory or time")
    def run(self,*,initial_state):
        sizes=self.estimate()
        decoded=q.Circuit.from_json(self._circuit)
        return evidence(decoded.run(initial_state=initial_state),self,64*1024**2,sizes)

def evaluate(n,gates,seed=1101,reps=7):
    rng=np.random.default_rng(seed);c=q.Circuit(n)
    for i in range(gates):
        w=i%n
        if i%3==0:c.ry(float(rng.uniform(-1,1)),w)
        elif i%3==1:c.cx(w,(w+1)%n)
        else:c.rz(float(rng.uniform(-1,1)),w)
    c.evolve(q.I(),time=.31) if n<=8 else None
    bits=["0"*n,"1"*n];paulis=["Z"*n,"X"*n];subsystems=[(n-1,0)]
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    builders={"previous":lambda:Previous(c,bits,paulis,subsystems),
              "current":lambda:c.plan(bits=bits,paulis=paulis,subsystems=subsystems)}
    plans={k:f() for k,f in builders.items()}
    reference=plans["previous"].run(initial_state=v)
    residual=compare_nested(reference,plans["current"].run(initial_state=v))
    assert residual<1e-9
    samples={k:{"prepare":[],"estimate":[],"run":[],"total_1":[],"total_4":[],"total_16":[]} for k in builders}
    rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(builders),2):
            plan,p=timed(builders[k]);samples[k]["prepare"].append(p)
            _,e=timed(plan.estimate);samples[k]["estimate"].append(e)
            elapsed=0.
            for i in range(16):
                out,t=timed(lambda:plan.run(initial_state=v));elapsed+=t
                samples[k]["run"].append(t)
                residual=max(residual,compare_nested(reference,out))
                if i+1 in (1,4,16):samples[k][f"total_{i+1}"].append(p+elapsed)
    assert residual<1e-9
    return dict(n=n,gates=gates,seed=seed,max_error=residual,
                variants={k:{name:stats(xs) for name,xs in stages.items()} for k,stages in samples.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,12):
        for gates in (32,256,1024):
            row=evaluate(n,gates,a.seed,3);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="legacy route emulation, upfront constructor and 1/4/16 runs; shared CI; no RSS claim",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
