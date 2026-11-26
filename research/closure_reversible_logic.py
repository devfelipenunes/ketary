"""Reversible increment, comparison and oracle composition, bounded local cases."""
import inspect
import json
import time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import IntegerComparator
from qiskit.quantum_info import Operator,Statevector
from research.abstraction_primitives import increment
from research.abstraction_advanced import truth_oracle
from research.circuit_rewrite_ladder import metrics,stats

def sdk_increment(n):
    return increment(n)

def native_increment(n):
    c=QuantumCircuit(n)
    for t in reversed(range(1,n)):c.mcx(list(range(t)),t)
    c.x(0)
    return c

def sdk_comparison(n,k):
    return truth_oracle(n,[format(i,f"0{n}b") for i in range(k,1<<n)])

def sdk_oracle_composition(n,k):
    a=truth_oracle(n,[format(i,f"0{n}b") for i in range(k,1<<n)])
    b=truth_oracle(n,[format(i,f"0{n}b") for i in range(1<<n) if i%2])
    return q.Circuit(n+1).apply(a).apply(b)

def native_truth(n,labels):
    c=QuantumCircuit(n+1)
    for label in labels:
        zeros=[i for i in range(n) if not (label>>i)&1]
        if zeros:c.x(zeros)
        c.mcx(list(range(n)),n)
        if zeros:c.x(zeros)
    return c

def native_comparison(n,k):
    return native_truth(n,range(k,1<<n))

def native_oracle_composition(n,k):
    c=native_truth(n,range(k,1<<n))
    c.compose(native_truth(n,range(1,1<<n,2)),inplace=True)
    return c

def library_comparator(n,k,expected):
    gate=IntegerComparator(num_state_qubits=n,value=k,geq=True)
    raw=QuantumCircuit(gate.num_qubits);raw.append(gate.to_gate(),range(gate.num_qubits))
    # Library has explicit work bits. Qualify the clean-work subspace only;
    # do not assume arbitrary work-bit inputs implement the same operator.
    u=Operator(raw).data
    d=len(expected)
    want=np.zeros((len(u),d),complex);want[:d,:]=expected
    np.testing.assert_allclose(u[:,:d],want,atol=1e-9,rtol=0)
    lowered=transpile(raw,basis_gates=["u","cx"],optimization_level=0,
                      seed_transpiler=1101,qubits_initially_zero=False)
    np.testing.assert_allclose(Operator(lowered).data[:,:d],want,atol=1e-9,rtol=0)
    return {"extra_work_wires":gate.num_qubits-(n+1),"common_basis_gates":len(lowered.data),
            "scope":"clean-work subspace; work bits returned to zero; not full arbitrary work inputs"}

def evaluate(kind,n,reps=3):
    if kind not in ("increment","comparison","composition") or n not in (2,3):raise ValueError("bounded fixture")
    k=(1<<n)//2+1
    if kind=="increment":
        builders={"sdk":sdk_increment,"native":native_increment};args=(n,);dim=1<<n
        mapping=[(i+1)%dim for i in range(dim)]
    else:
        builders={"sdk":sdk_comparison if kind=="comparison" else sdk_oracle_composition,
                  "native":native_comparison if kind=="comparison" else native_oracle_composition}
        args=(n,k);dim=1<<(n+1)
        mapping=[]
        for i in range(dim):
            a=i&((1<<n)-1)
            bit=(a>=k)^bool(a%2) if kind=="composition" else a>=k
            mapping.append(i^(int(bit)<<n))
    expected=np.zeros((dim,dim),complex)
    expected[mapping,np.arange(dim)]=1
    rng=np.random.default_rng(1101+n);v=rng.normal(size=dim)+1j*rng.normal(size=dim);v/=np.linalg.norm(v)
    paths={}
    for mode,fn in builders.items():
        c=fn(*args);raw=c.to_qiskit() if mode=="sdk" else c
        common=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=1101,qubits_initially_zero=False)
        for a in (raw,common):np.testing.assert_allclose(Operator(a).data,expected,atol=1e-9,rtol=0)
        np.testing.assert_allclose(Operator(raw.inverse()).data,expected.conj().T,atol=1e-9,rtol=0)
        source=inspect.getsource(fn)
        paths[mode]=dict(source=source,metrics=metrics(source),logical_gates=len(raw.data),common_basis_gates=len(common.data),
                         common_basis_depth=common.depth(),build=[],run=[])
    for i in range(reps):
        for mode in (("sdk","native") if i%2==0 else ("native","sdk")):
            start=time.perf_counter_ns();c=builders[mode](*args);mid=time.perf_counter_ns()
            out=c.run(initial_state=v).math.statevector() if mode=="sdk" else Statevector(v).evolve(c).data.copy()
            end=time.perf_counter_ns()
            np.testing.assert_allclose(out,expected@v,atol=1e-9,rtol=0)
            paths[mode]["build"].append((mid-start)/1e6);paths[mode]["run"].append((end-mid)/1e6)
    for row in paths.values():
        for key in ("build","run"):row[key]=stats(row[key])
    return dict(kind=kind,n=n,threshold=k,paths=paths,library=library_comparator(n,k,expected) if kind=="comparison" else None,
                scope="all basis columns incl occupied output, strict complex input, modular overflow; helper source costs excluded from wrappers; no runtime API promotion")

if __name__=="__main__":
    print(json.dumps([evaluate(k,n) for k in ("increment","comparison","composition") for n in (2,3)],indent=2,allow_nan=False))
