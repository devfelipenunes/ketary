"""API03: compare independent parameter workloads, not sequential circuits.

One set of numeric rows and one exact ordered gate template. Timings include
all binding/construction or all explicit execution; copied outputs in each
path. Authored diagnostic, not independent user or hardware evidence.
"""
import argparse,json,random,statistics,time,platform
from pathlib import Path
from importlib.metadata import version
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Operator,Statevector

def cases(n,rows,seed,reps=7):
    rng=np.random.default_rng(seed)
    values=rng.uniform(-1,1,(rows,n+1)).tolist()
    edges=[(i,i+1) for i in range(n-1)]
    # Share the last parameter deliberately across every pair.
    theta=q.Circuit.parameter_vector("t",n+1)
    template=q.Circuit.symbolic(n).ry(theta[:n],range(n)).rzz(theta[-1],pairs=edges)
    native_theta=ParameterVector("t",n+1)
    native=QuantumCircuit(n)
    for i in range(n):native.ry(native_theta[i],i)
    for a,b in edges:native.rzz(native_theta[-1],a,b)
    def manual():
        return tuple(q.Circuit(n).ry(row[:n],range(n)).rzz(row[-1],pairs=edges) for row in values)
    def identity():
        return tuple(template.bind(dict(zip(theta,row,strict=True))) for row in values)
    def ordered():
        # ParameterVector uses native vector index ordering, not string sort.
        return tuple(template.bind(row) for row in values)
    def sweeps():
        return template.sweep_rows(values)
    def qiskit_bound():
        return tuple(native.assign_parameters(dict(zip(native_theta,row,strict=True))) for row in values)
    builders={"manual":manual,"identity":identity,"ordered":ordered,"sweep_rows":sweeps,"qiskit":qiskit_bound}
    expected=qiskit_bound()
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    # SweepPlan.run currently starts from zero. Compare *all* execution
    # variants on zero; complex inputs separately validate bound operators.
    def execute(name,artifact):
        if name=="sweep_rows":return tuple(x.math.statevector() for x in artifact.run())
        if name=="qiskit":return tuple(Statevector.from_instruction(x).data.copy() for x in artifact)
        return tuple(c.run().math.statevector() for c in artifact)
    target=execute("qiskit",expected)
    error={}
    for name,build in builders.items():
        artifact=build()
        got=execute(name,artifact)
        assert len(got)==len(target)
        residual=max(float(np.max(np.abs(a-b))) for a,b in zip(got,target,strict=True))
        if name!="sweep_rows":
            for c,ref in zip(artifact,expected,strict=True):
                raw=c if name=="qiskit" else c.to_qiskit()
                residual=max(residual,float(np.max(np.abs(Operator(raw).data-Operator(ref).data))),
                             float(np.max(np.abs(Statevector(v).evolve(raw).data-Statevector(v).evolve(ref).data))))
        if residual>1e-9:raise AssertionError(f"{name}: {residual}")
        error[name]=residual
    samples={name:{"build":[],"run":[]} for name in builders};order_rng=random.Random(seed)
    for _ in range(reps):
        order=list(builders);order_rng.shuffle(order)
        for name in order:
            t=time.perf_counter_ns();artifact=builders[name]();samples[name]["build"].append((time.perf_counter_ns()-t)/1e6)
            t=time.perf_counter_ns();execute(name,artifact);samples[name]["run"].append((time.perf_counter_ns()-t)/1e6)
    return dict(n=n,rows=rows,variants={name:dict(max_error=error[name],**{k:dict(raw_ms=xs,p50_ms=statistics.median(xs),p95_ms=float(np.quantile(xs,.95))) for k,xs in stages.items()}) for name,stages in samples.items()},
                scope="independent zero-input outputs; strict bound operators and complex input except sweep public output only; template construction excluded")
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);p.add_argument("--reps",type=int,default=7);a=p.parse_args()
    if not 3<=a.reps<=30:p.error("3..30 repetitions")
    results=[]
    for n in (2,4,6):
        for count in (1,8,32):
            row=cases(n,count,a.seed,a.reps);results.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(seed=a.seed,python=platform.python_version(),qiskit=version("qiskit"),rows=results),indent=2,allow_nan=False))
if __name__=="__main__":main()
