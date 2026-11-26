"""Cross-workflow local observable reuse; research-only, matched outputs."""
import argparse,json,random,statistics,time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp,Statevector
from scipy.linalg import expm
from research.observable_reuse import embed
from research.circuit_rewrite_ladder import metrics
from research.workflow_depth import dense,label

MANUAL={
"read":"""H=sum(.7*(q.Y(a)@q.X(b))-.4*(q.X(a)@q.Y(b))+.2*q.I()+.3*q.Z(a) for a,b in placements)
r=q.Result(v)
out=(r.math.expectation(H),r.math.variance(H))""",
"evolve":"""H=sum(.7*(q.Y(a)@q.X(b))-.4*(q.X(a)@q.Y(b))+.2*q.I() for a,b in placements)
c=q.Circuit(n).evolve(H,time=t)
r=c.run(initial_state=v)
out=(r.math.statevector(),r.math.expectation(H))"""
}
CANDIDATE={
"read":"""H=sum(embed(local,wires,width=n) for wires in placements)
r=q.Result(v)
out=(r.math.expectation(H),r.math.variance(H))""",
"evolve":"""H=sum(embed(local,wires,width=n) for wires in placements)
c=q.Circuit(n).evolve(H,time=t)
r=c.run(initial_state=v)
out=(r.math.statevector(),r.math.expectation(H))"""
}
NATIVE={
"read":"""H=SparsePauliOp.from_list(terms)
r=Statevector(v)
e=float(r.expectation_value(H).real)
out=(e,float(r.expectation_value(H@H).real-e*e))""",
"evolve":"""H=SparsePauliOp.from_list(terms)
c=QuantumCircuit(n)
c.append(PauliEvolutionGate(H,time=t),range(n))
r=Statevector(v).evolve(c)
out=(r.data.copy(),float(r.expectation_value(H).real))"""
}
def evaluate(kind,n,seed=1101,reps=7):
    rng=np.random.default_rng(seed)
    placements=[(n-1,0),(1,n-2)]
    mapping={"XY":.7,"YX":-.4,"II":.2}
    if kind=="read":mapping["IZ"]=.3
    local=q.Observable(mapping)
    terms=[]
    for a,b in placements:
        terms.extend([(label(n,{a:"Y",b:"X"}),.7),(label(n,{a:"X",b:"Y"}),-.4),("I"*n,.2)])
        if kind=="read":terms.append((label(n,{a:"Z"}),.3))
    combined={}
    for k,w in terms:combined[k]=combined.get(k,0.)+w
    terms=list(combined.items())
    H=dense(combined)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    t=.37
    if kind=="read":
        hv=H@v;e=float(np.vdot(v,hv).real);expected=(e,float(np.vdot(hv,hv).real-e*e))
    else:
        state=expm(-1j*t*H)@v;expected=(state,float(np.vdot(state,H@state).real))
    sources={"manual":MANUAL[kind],"embedding":CANDIDATE[kind],"qiskit":NATIVE[kind]}
    env=dict(q=q,embed=embed,local=local,n=n,placements=placements,v=v,t=t,terms=terms,
             QuantumCircuit=QuantumCircuit,PauliEvolutionGate=PauliEvolutionGate,SparsePauliOp=SparsePauliOp,Statevector=Statevector)
    compiled={k:compile(s,"<reviewed-reuse>","exec") for k,s in sources.items()}
    def run(k):
        scope=env.copy();start=time.perf_counter_ns();exec(compiled[k],scope)
        return scope["out"],(time.perf_counter_ns()-start)/1e6
    errors={};samples={k:[] for k in sources}
    for k in sources:
        out,_=run(k);errors[k]=max(float(np.max(np.abs(a-b))) for a,b in zip(out,expected,strict=True))
        if errors[k]>1e-9:raise AssertionError((kind,k,errors[k]))
    rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(sources),len(sources)):
            _,ms=run(k);samples[k].append(ms)
    return dict(kind=kind,n=n,seed=seed,variants={k:dict(source=s,**metrics(s),max_error=errors[k],raw_ms=samples[k],p50_ms=statistics.median(samples[k]),p95_ms=float(np.quantile(samples[k],.95))) for k,s in sources.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for kind in ("read","evolve"):
        for n in (4,6,8):
            row=evaluate(kind,n,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="authored workflow snippets; shared local observable and native term inputs excluded, no independent users",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
