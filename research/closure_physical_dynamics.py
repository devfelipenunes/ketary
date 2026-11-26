"""Five matched local physical dynamics applications, exact bounded segments."""
import inspect
import itertools
import json
import time
import numpy as np
from scipy.linalg import expm
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import HamiltonianGate
from qiskit.quantum_info import Operator,Statevector,SparsePauliOp
from research.circuit_rewrite_ladder import metrics,stats

CASES={
    "ising_quench":(3,(({"ZZI":.7,"IZZ":.7,"XII":.4,"IXI":.4,"IIX":.4},.31),)),
    "xy_exchange":(2,(({"XX":.6,"YY":.6},.47),)),
    "heisenberg_chain":(3,(({"XXI":.3,"YYI":.3,"ZZI":.3,"IXX":.5,"IYY":.5,"IZZ":.5},.25),)),
    "diagonal":(3,(({"III":.2,"ZZI":-.7,"IZZ":.4,"ZIZ":.3,"IIZ":.1},-.37),)),
    "piecewise":(2,(({"XI":.6,"IZ":.2},.29),({"ZZ":.7,"IX":-.3},.43),({"XI":-.2,"II":.11},.17))),
}
PAULI={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),
       "Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1.,-1.])}

def dense(terms):
    out=np.zeros((2**len(next(iter(terms))),)*2,complex)
    for label,coef in terms.items():
        m=np.ones((1,1),complex)
        for a in label:m=np.kron(m,PAULI[a])
        out+=coef*m
    return out

def sdk(n,segments,commuting):
    c=q.Circuit(n)
    for terms,t in segments:
        H=q.Observable(terms)
        if commuting:c.evolve(H,time=t)
        else:c.evolve_exact(H,time=t,seed=1101)
    return c

def native(n,segments,commuting):
    c=QuantumCircuit(n)
    for terms,t in segments:
        # Native dense HamiltonianGate avoids the incompatible MatrixExponential
        # HLS preserve_order argument. Still exact, not a product formula.
        c.append(HamiltonianGate(dense(terms),time=t),range(n))
    return c

def evaluate(name,seed=1101,reps=3):
    n,segments=CASES[name];commuting=name in ("diagonal","xy_exchange")
    ref=np.eye(1<<n,dtype=complex)
    for terms,t in segments:ref=expm(-1j*t*dense(terms))@ref
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    expected=ref@v;H=dense(segments[-1][0])
    energy=float(np.vdot(expected,H@expected).real)
    paths={}
    for mode,fn in (("sdk",sdk),("native",native)):
        c=fn(n,segments,commuting);raw=c.to_qiskit() if mode=="sdk" else c
        lowered=transpile(raw,basis_gates=["u","cx"],optimization_level=0,
                          seed_transpiler=seed,qubits_initially_zero=False)
        for a in (raw,lowered):
            np.testing.assert_allclose(Operator(a).data,ref,atol=1e-9,rtol=0)
        source=inspect.getsource(fn)
        paths[mode]=dict(source=source,metrics=metrics(source),logical_gates=len(raw.data),
                         common_basis_gates=len(lowered.data),common_basis_depth=lowered.depth(),build=[],run=[])
    for i in range(reps):
        for mode,fn in ((("sdk",sdk),("native",native)) if i%2==0 else (("native",native),("sdk",sdk))):
            start=time.perf_counter_ns();c=fn(n,segments,commuting);mid=time.perf_counter_ns()
            if mode=="sdk":
                r=c.run(initial_state=v);state=r.math.statevector()
                value=r.math.expectation(q.Observable(segments[-1][0]))
            else:
                r=Statevector(v).evolve(c);state=r.data.copy()
                value=float(r.expectation_value(SparsePauliOp.from_list(list(segments[-1][0].items()))).real)
            end=time.perf_counter_ns()
            np.testing.assert_allclose(state,expected,atol=1e-9,rtol=0)
            assert abs(value-energy)<1e-9
            paths[mode]["build"].append((mid-start)/1e6);paths[mode]["run"].append((end-mid)/1e6)
    for row in paths.values():
        for key in ("build","run"):row[key]=stats(row[key])
    return dict(case=name,n=n,seed=seed,segments=segments,energy=energy,paths=paths,
                scope="small exact unitary segments; dense oracle, common basis strict phase; shared host; no continuous time approximation or physical device claim")

def run():
    return [evaluate(name,seed) for name,seed in itertools.product(CASES,(1101,2202,3303))]

if __name__=="__main__":
    print(json.dumps(run(),indent=2,allow_nan=False))
