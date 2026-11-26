"""Matched modular adders: authored local CPU diagnostic, no new installed API."""
import inspect,json,time
import numpy as np
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import ModularAdderGate
from qiskit.quantum_info import Operator,Statevector
from research.abstraction_advanced import add_register
from research.circuit_rewrite_ladder import metrics,stats

def sdk(n):
    return add_register(n)

def native(n):
    c=QuantumCircuit(2*n)
    c.append(ModularAdderGate(n),range(2*n))
    return c

def evaluate(n,reps=3):
    if n not in (1,2,3,4) or not 2<=reps<=20:raise ValueError("bounded diagnostic")
    size=1<<n;dim=size**2
    expected=np.zeros((dim,dim),complex)
    for i in range(dim):
        a,b=i%size,i//size
        expected[a+size*((a+b)%size),i]=1
    rng=np.random.default_rng(1101+n)
    v=rng.normal(size=dim)+1j*rng.normal(size=dim);v/=np.linalg.norm(v)
    rows={}
    for name,fn in (("sdk",sdk),("native",native)):
        built=fn(n);raw=built.to_qiskit() if name=="sdk" else built
        np.testing.assert_allclose(Operator(raw).data,expected,atol=1e-9,rtol=0)
        lowered=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=1101,qubits_initially_zero=False)
        np.testing.assert_allclose(Operator(lowered).data,expected,atol=1e-9,rtol=0)
        source=inspect.getsource(add_register if name=="sdk" else fn)
        rows[name]={"source":source,"metrics":metrics(source),"logical":len(raw.data),"basis":len(lowered.data),"basis_depth":lowered.depth(),"build":[],"run":[]}
    for i in range(reps):
        for name,fn in ((("sdk",sdk),("native",native)) if i%2==0 else (("native",native),("sdk",sdk))):
            start=time.perf_counter_ns();c=fn(n);mid=time.perf_counter_ns()
            out=c.run(initial_state=v).math.statevector() if name=="sdk" else Statevector(v).evolve(c).data.copy()
            end=time.perf_counter_ns()
            np.testing.assert_allclose(out,expected@v,atol=1e-9,rtol=0)
            rows[name]["build"].append((mid-start)/1e6);rows[name]["run"].append((end-mid)/1e6)
    for row in rows.values():
        for key in ("build","run"):row[key]=stats(row[key])
    return {"n":n,"paths":rows,"scope":"modular two-register addition, all basis columns and arbitrary complex input; helper _mcx cost excluded from source metric; no carry-out, comparator or hardware claim"}

if __name__=="__main__":
    print(json.dumps([evaluate(n) for n in (1,2,3,4)],indent=2))
