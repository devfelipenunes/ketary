"""Matched end-to-end workloads and gradient counterexample, authored in-house.

No installed APIs, no user study. Compare complete mathematical objectives
and complex states, including phase. Timings include source construction and
objective evaluation separately; shared runners are diagnostic.
"""
import argparse,json,random,statistics,time,platform
from pathlib import Path
from importlib.metadata import version
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import Statevector,SparsePauliOp
from scipy.linalg import expm
from research.circuit_rewrite_ladder import metrics

QAOA_K="""p=q.Circuit.parameter_vector('p',4)
H=q.maxcut_hamiltonian(n,edges,weights=weights)
M=sum(q.X(i) for i in range(n))
c=q.Circuit.symbolic(n).h(range(n))
for j in range(2):
    c.evolve(H,time=p[2*j]).evolve(M,time=p[2*j+1])
results=c.sweep_rows(rows).run()
out=[(r.math.statevector(),r.math.expectation(H),r.math.variance(H)) for r in results]"""
QAOA_Q="""p=ParameterVector('p',4)
H=SparsePauliOp.from_list(cost_terms)
M=SparsePauliOp.from_list(mixer_terms)
c=QuantumCircuit(n)
c.h(range(n))
for j in range(2):
    c.append(PauliEvolutionGate(H,time=p[2*j]),range(n))
    c.append(PauliEvolutionGate(M,time=p[2*j+1]),range(n))
results=[Statevector.from_instruction(c.assign_parameters(dict(zip(p,row,strict=True)))) for row in rows]
out=[(r.data.copy(),float(r.expectation_value(H).real),float(r.expectation_value(H@H).real-r.expectation_value(H).real**2)) for r in results]"""
VQE_K="""p=q.Circuit.parameter_vector('p',2*n)
H=q.Observable(terms)
c=q.Circuit.symbolic(n)
for j in range(2):
    c.ry(p[j*n:(j+1)*n],range(n)).cx(pairs=q.chain(range(n)))
results=c.sweep_rows(rows).run()
out=[(r.math.statevector(),r.math.expectation(H),r.math.variance(H)) for r in results]"""
VQE_Q="""p=ParameterVector('p',2*n)
H=SparsePauliOp.from_list(list(terms.items()))
c=QuantumCircuit(n)
for j in range(2):
    for i in range(n):c.ry(p[j*n+i],i)
    c.cx(list(range(n-1)),list(range(1,n)))
results=[Statevector.from_instruction(c.assign_parameters(dict(zip(p,row,strict=True)))) for row in rows]
out=[(r.data.copy(),float(r.expectation_value(H).real),float(r.expectation_value(H@H).real-r.expectation_value(H).real**2)) for r in results]"""
def pauli(label):
    P={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    out=np.array([[1.]])
    for axis in label:out=np.kron(out,P[axis])
    return out
def dense(terms):return sum(v*pauli(k) for k,v in terms.items())
def label(n,axes):
    return "".join(axes.get(i,"I") for i in reversed(range(n)))
def oracle(kind,n,rows,terms,mixer=None):
    H=dense(terms);outputs=[]
    for row in rows:
        v=np.ones(1<<n,complex)/np.sqrt(1<<n) if kind=="qaoa" else np.eye(1<<n,dtype=complex)[:,0]
        for j in range(2):
            if kind=="qaoa":
                v=expm(-1j*row[2*j+1]*mixer)@(expm(-1j*row[2*j]*H)@v)
            else:
                local=np.array([[1.]])
                for t in reversed(row[j*n:(j+1)*n]):
                    local=np.kron(local,[[np.cos(t/2),-np.sin(t/2)],[np.sin(t/2),np.cos(t/2)]])
                v=local@v
                for i in range(n-1):
                    # CNOT truth table independent of Qiskit or Ketary.
                    perm=[k^(((k>>i)&1)<<(i+1)) for k in range(1<<n)]
                    v=v[perm]
        hv=H@v;e=float(np.vdot(v,hv).real)
        outputs.append((v,e,float(np.vdot(hv,hv).real-e*e)))
    return outputs
def evaluate(kind,n,seed=1101,count=3,reps=5):
    rng=np.random.default_rng(seed)
    edges=[(i,i+1) for i in range(n-1)]+[(0,n-1)]
    weights=[.3+.2*i for i in range(len(edges))]
    cost_terms=[("I"*n,sum(weights)/2)]+[(label(n,{a:"Z",b:"Z"}),-w/2) for (a,b),w in zip(edges,weights,strict=True)]
    mixer_terms=[(label(n,{i:"X"}),1.) for i in range(n)]
    terms={label(n,{0:"X"}):.7,label(n,{0:"Z",1:"Z"}):-.4,label(n,{n-1:"Y"}):.3,"I"*n:.2}
    rows=rng.uniform(-.8,.8,(count,4 if kind=="qaoa" else 2*n)).tolist()
    expected=oracle(kind,n,rows,dict(cost_terms) if kind=="qaoa" else terms,dense(dict(mixer_terms)) if kind=="qaoa" else None)
    sources={"ketary":QAOA_K if kind=="qaoa" else VQE_K,"qiskit":QAOA_Q if kind=="qaoa" else VQE_Q}
    env=dict(q=q,np=np,QuantumCircuit=QuantumCircuit,ParameterVector=ParameterVector,
             PauliEvolutionGate=PauliEvolutionGate,Statevector=Statevector,SparsePauliOp=SparsePauliOp,n=n,
             edges=edges,weights=weights,cost_terms=cost_terms,mixer_terms=mixer_terms,terms=terms,rows=rows)
    # Split source at the explicit results= boundary, keeping objective
    # execution and snapshot export in the second stage.
    compiled={}
    for key,source in sources.items():
        a,b=source.split("\nresults=",1)
        compiled[key]=(compile(a,"<build>","exec"),compile("results="+b,"<objective>","exec"))
    def run(key):
        a,b=compiled[key];scope=env.copy()
        t=time.perf_counter_ns();exec(a,scope);build=(time.perf_counter_ns()-t)/1e6
        t=time.perf_counter_ns();exec(b,scope);execute=(time.perf_counter_ns()-t)/1e6
        return scope["out"],build,execute
    errors={};samples={k:{"build":[],"objective":[]} for k in sources}
    for key in sources:
        got,_,_=run(key);assert len(got)==len(expected)
        errors[key]=max(max(float(np.max(np.abs(x-y))) for x,y in zip(a,b,strict=True)) for a,b in zip(got,expected,strict=True))
        if errors[key]>1e-9:raise AssertionError((kind,key,errors[key]))
    rnd=random.Random(seed)
    for _ in range(reps):
        order=list(sources);rnd.shuffle(order)
        for k in order:
            _,build,execute=run(k);samples[k]["build"].append(build);samples[k]["objective"].append(execute)
    return dict(kind=kind,n=n,seed=seed,rows=count,variants={k:dict(source=sources[k],**metrics(sources[k]),max_error=errors[k],**{name:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for name,v in sample.items()}) for k,sample in samples.items()})
def gradient_counterexample(t=.37):
    """Shared parameter: naive single two-point shift is not general."""
    a=q.Circuit.parameter("a")
    c=q.Circuit.symbolic(1).ry(a,0).ry(a,0)
    def f(x):return c.bind([x]).run().math.expectation("Z")
    naive=(f(t+np.pi/2)-f(t-np.pi/2))/2
    finite=(f(t+1e-5)-f(t-1e-5))/(2e-5)
    p=q.Circuit.parameter_vector("p",2)
    split=q.Circuit.symbolic(1).ry(p[0],0).ry(p[1],0)
    def g(x,y):return split.bind([x,y]).run().math.expectation("Z")
    occurrence=(g(t+np.pi/2,t)-g(t-np.pi/2,t)+g(t,t+np.pi/2)-g(t,t-np.pi/2))/2
    return dict(naive=naive,finite_difference=finite,occurrence_sum=occurrence,analytic=-2*np.sin(2*t))
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for kind in ("qaoa","vqe"):
        for n in (3,4,5):
            row=evaluate(kind,n,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="authored objective workflows; shared CI diagnostic; no independent users",python=platform.python_version(),qiskit=version("qiskit"),rows=rows,gradient=gradient_counterexample()),indent=2,allow_nan=False))
if __name__=="__main__":main()
