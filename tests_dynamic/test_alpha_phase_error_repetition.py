"""Phase-flip repetition code, not general fault tolerance."""
import numpy as np
import pytest
from qiskit import QuantumCircuit,transpile
from qiskit_aer import AerSimulator
import ketary as q

@pytest.mark.parametrize("error",[None,0,1,2])
@pytest.mark.parametrize("axis",["X","Y","Z"])
def test_phase_error_repetition(error,axis):
    theta,phi=.91,-.63
    c=QuantumCircuit(5,3)
    c.ry(theta,0);c.rz(phi,0)
    c.cx(0,1);c.cx(0,2);c.h([0,1,2])
    if error is not None:c.z(error)
    c.h([0,1,2])
    c.cx(0,3);c.cx(1,3);c.cx(1,4);c.cx(2,4)
    c.measure(3,0);c.measure(4,1)
    # Measured two-bit syndrome, output bit still zero. Explicit local
    # gate-only feed-forward through the documented native boundary.
    for syndrome,wire in ((1,0),(3,1),(2,2)):
        with c.if_test((c.cregs[0],syndrome)):c.x(wire)
    c.cx(0,2);c.cx(0,1)
    if axis=="Y":c.sdg(0)
    if axis in ("X","Y"):c.h(0)
    c.measure(0,2)
    shots=2048;seed=2202
    a=q.Circuit.from_dynamic(c).run_shots(shots=shots,seed=seed).counts
    aer=AerSimulator(method="statevector",max_parallel_threads=1)
    b=aer.run(transpile(c,aer,optimization_level=0,seed_transpiler=seed),shots=shots,seed_simulator=seed).result().get_counts()
    syndrome={None:"00",0:"01",1:"11",2:"10"}[error]
    expected={"X":np.sin(theta)*np.cos(phi),"Y":np.sin(theta)*np.sin(phi),"Z":np.cos(theta)}[axis]
    for counts in (a,b):
        assert sum(counts.values())==shots and all(k[1:]==syndrome for k in counts)
        assert abs(sum((1 if k[0]=="0" else -1)*v for k,v in counts.items())/shots-expected)<.12
