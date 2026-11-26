"""Bounded repetition code: single X errors, ideal local dynamic simulation."""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile
import ketary as q

def native(error,axis):
    theta,phi=.91,-.63
    c=QuantumCircuit(5,3)
    c.ry(theta,0);c.rz(phi,0)
    c.cx(0,1);c.cx(0,2)
    if error is not None:c.x(error)
    c.cx(0,3);c.cx(1,3)
    c.cx(1,4);c.cx(2,4)
    c.measure(3,0);c.measure(4,1)
    # Syndrome c1c0: 01 -> wire 0, 11 -> wire 1, 10 -> wire 2.
    # Compare two-bit register values while output bit is initially zero.
    for syndrome,wire in ((1,0),(3,1),(2,2)):
        with c.if_test((c.cregs[0],syndrome)):
            c.x(wire)
    c.cx(0,2);c.cx(0,1)
    if axis=="Y":c.sdg(0)
    if axis in ("X","Y"):c.h(0)
    c.measure(0,2)
    return c

@pytest.mark.parametrize("error",[None,0,1,2])
@pytest.mark.parametrize("axis",["X","Y","Z"])
def test_repetition_code_syndrome(error,axis):
    raw=native(error,axis)
    sdk=q.Circuit.from_dynamic(raw)
    shots=2048;seed=1101
    counts=sdk.run_shots(shots=shots,seed=seed).counts
    aer=AerSimulator(method="statevector",max_parallel_threads=1)
    compiled=transpile(raw,aer,optimization_level=0,seed_transpiler=seed)
    reference=aer.run(compiled,shots=shots,seed_simulator=seed).result().get_counts()
    syndrome={None:"00",0:"01",1:"11",2:"10"}[error]
    theta,phi=.91,-.63
    expected={"X":np.sin(theta)*np.cos(phi),"Y":np.sin(theta)*np.sin(phi),"Z":np.cos(theta)}[axis]
    for observed in (counts,reference):
        assert sum(observed.values())==shots
        assert all(label[1:]==syndrome for label in observed)
        expectation=sum((1 if label[0]=="0" else -1)*count for label,count in observed.items())/shots
        # Fixed seed and conservative diagnostic threshold; no process fidelity claim.
        assert abs(expectation-expected)<.12
