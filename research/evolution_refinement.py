"""RF07–10: compare native gates, earlier prototype and exact public evolve.

All expressions are authored static fixtures, not arbitrary code input.
Compare the same operator, phase and initial state, not just probabilities.
"""
import argparse,json,random,time,platform
from importlib.metadata import version
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import Operator,SparsePauliOp
from scipy.linalg import expm
from research import abstraction_primitives as p
from research.circuit_rewrite_ladder import metrics,native,state,stats

KEYS=("manual","prototype","public","qiskit")
# All sources receive the same Hamiltonian H and time t. Manual code
# includes phase management where no existing public global phase setter
# was available. Native PauliEvolutionGate is an idiomatic library baseline.
CASES=[
("mixed_xz",2,{"ZX":.5},
 "c=q.Circuit(n).h(0).cx(0,1).rz(t,1).cx(0,1).h(0)",
 "c=p.evolve(H,t,n=n)","c=q.Circuit(n).evolve(H,time=t)"),
("weighted_zz",3,{"IZZ":.7,"ZZI":-.4},
 "c=q.Circuit(n).rzz([1.4*t,-.8*t],pairs=[(0,1),(1,2)])",
 "c=p.evolve(H,t,n=n)","c=q.Circuit(n).evolve(H,time=t)"),
("x_mixer",4,{"IIIX":1,"IIXI":1,"IXII":1,"XIII":1},
 "c=q.Circuit(n).rx(2*t,range(n))",
 "c=p.evolve(H,t,n=n)","c=q.Circuit(n).evolve(H,time=t)"),
("commuting_xyz",2,{"XX":.7,"YY":-.31,"ZZ":.21},
 "c=q.Circuit(n).rxx(1.4*t,0,1).ryy(-.62*t,0,1).rzz(.42*t,0,1)",
 "c=p.evolve(H,t,n=n)","c=q.Circuit(n).evolve(H,time=t)"),
("identity_phase",2,{"II":.9,"ZZ":.5},
 "c=q.from_qiskit(QuantumCircuit(n,global_phase=-.9*t)).rzz(t,0,1)",
 "c=p.evolve(H,t,n=n)","c=q.Circuit(n).evolve(H,time=t)"),
("mixed_three",3,{"XYZ":.5},
 "c=q.Circuit(n).sdg(1).h([1,2]).cx(0,2).cx(1,2).rz(t,2).cx(1,2).cx(0,2).h([2,1]).s(1)",
 "c=p.evolve(H,t,n=n)","c=q.Circuit(n).evolve(H,time=t)"),
]
NATIVE="c=QuantumCircuit(n); c.append(PauliEvolutionGate(H.to_qiskit(n),time=t),range(n))"
def evaluate(case,seed=1101,reps=7,t=.37):
    name,n,terms,*sources=case;sources+= [NATIVE]
    H=q.Observable(terms)
    dense=H.to_qiskit(n).to_matrix()
    ref=expm(-1j*t*dense)
    rng=np.random.default_rng(seed);v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    def make(source):
        code=compile(source,"<reviewed-evolution>","exec")
        def build():
            scope=dict(q=q,p=p,H=H,t=t,n=n,QuantumCircuit=QuantumCircuit,PauliEvolutionGate=PauliEvolutionGate)
            exec(code,scope);return scope["c"]
        return build
    builders=dict(zip(KEYS,map(make,sources),strict=True))
    results={}
    for k,s in zip(KEYS,sources,strict=True):
        c=builders[k]();raw=native(c)
        expanded=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
        err=max(float(np.max(np.abs(Operator(raw).data-ref))),float(np.max(np.abs(Operator(expanded).data-ref))),float(np.max(np.abs(state(c,v)-ref@v))))
        if err>1e-9:raise AssertionError(f"{name}/{k}: strict residual {err}")
        results[k]=dict(source=s,**metrics(s),logical_gates=len(raw.data),basis_gates=len(expanded.data),basis_depth=expanded.depth(),max_error=err,build=[],run=[])
    order_rng=random.Random(seed)
    for _ in range(reps):
        order=list(KEYS);order_rng.shuffle(order)
        for k in order:
            start=time.perf_counter_ns();c=builders[k]();results[k]["build"].append((time.perf_counter_ns()-start)/1e6)
            start=time.perf_counter_ns();state(c,v);results[k]["run"].append((time.perf_counter_ns()-start)/1e6)
    for row in results.values():
        for key in ("build","run"):row[key]=stats(row[key])
    return dict(name=name,time=t,variants=results)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True);parser.add_argument("--seed",type=int,default=1101);parser.add_argument("--reps",type=int,default=7);a=parser.parse_args()
    if not 3<=a.reps<=30:parser.error("3..30 repetitions")
    rows=[]
    for case in CASES:
        for t in (.37,-.29):
            row=evaluate(case,a.seed,a.reps,t);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="authored commuting evolution; shared CI diagnostic",python=platform.python_version(),qiskit=version("qiskit"),seed=a.seed,rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
