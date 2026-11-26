import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("n",[2,3,4,5])
def test_marked_mask_transitions(n):
    labels=[format(i,f"0{n}b") for i in (0,1,3,2)]
    c=q.phase_oracle(labels);raw=c.to_qiskit()
    expected=np.eye(1<<n,dtype=complex)
    for label in labels:expected[int(label,2),int(label,2)]=-1
    np.testing.assert_allclose(Operator(raw).data,expected,atol=1e-9,rtol=0)
    old_x=2*sum(label.count("0") for label in labels)
    assert raw.count_ops().get("x",0)<old_x
    v=np.arange(1,1+(1<<n))+1j*np.arange(1<<n);v=v/np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),expected@v,atol=1e-9,rtol=0)

@pytest.mark.parametrize("state",[0,1])
@pytest.mark.parametrize("phase",[0.,.31,-.72])
@pytest.mark.parametrize("wires",[(),(0,),(2,1,2)])
def test_controlled_x_phase_strict(state,phase,wires):
    source=q.Circuit(3)
    for w in wires:source.x(w)
    source.evolve(q.I(),time=phase)
    before=source.to_qiskit()
    c=source.control(control_state=state)
    matrix=np.eye(16,dtype=complex)
    U=Operator(before).data
    indices=[2*i+state for i in range(8)]
    matrix[np.ix_(indices,indices)]=U
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,matrix,atol=1e-9,rtol=0)
    assert set(c.to_qiskit().count_ops())<={"u","cx"}
    assert source.to_qiskit()==before

def test_control_seed_preflight():
    for seed in (-1,2**32,True):
        with pytest.raises(ValueError):q.Circuit(1).control(seed=seed)

@pytest.mark.parametrize("columns",[False,True])
def test_sweep_rechecks_mutated_source_before_binding(columns,monkeypatch):
    p=q.Circuit.parameter("p");c=q.Circuit.symbolic(1).rx(p,0)
    def rows():
        yield .2 if columns else [.2]
        for _ in range(256):c.h(0)
    monkeypatch.setattr(q.Circuit,"_bind_numeric",lambda *a:pytest.fail("native binding before final source cap"))
    with pytest.raises(q.ResourceLimit):
        c.sweep(p=rows()) if columns else c.sweep_rows(rows())
