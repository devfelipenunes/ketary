import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Operator
from research.native_adjacent_gate_fusion import fuse,evaluate

@pytest.mark.parametrize("name",["rx","ry","rz","p","rxx","ryy","rzz"])
def test_numeric_rotation_phase(name):
    c=QuantumCircuit(2,global_phase=.37)
    wires=(1,0) if len(name)==3 and name.startswith("r") else (1,)
    if name in ("rxx","ryy","rzz"):wires=(1,0)
    getattr(c,name)(2*np.pi,*wires);getattr(c,name)(.31,*wires)
    out=fuse(c)
    assert len(out.data)==1
    np.testing.assert_allclose(Operator(out).data,Operator(c).data,atol=1e-9,rtol=0)

def test_symbolic_identity_and_cancellation():
    t=Parameter("t");p=Parameter("p")
    c=QuantumCircuit(2,global_phase=.3);c.rx(t,0);c.rx(p,0);c.ry(t,1);c.ry(-t,1)
    out=fuse(c);assert set(out.parameters)=={t,p}
    for values in ((.3,.7),(-.2,1.1)):
        mapping=dict(zip((t,p),values,strict=True))
        np.testing.assert_allclose(Operator(out.assign_parameters(mapping)).data,Operator(c.assign_parameters(mapping)).data,atol=1e-9,rtol=0)

def test_order_and_distinct_operands():
    c=QuantumCircuit(2);c.cx(0,1);c.cx(1,0);c.h(0);c.z(0);c.h(0)
    assert fuse(c)==c

def test_negative_unsupported_classical_and_barrier():
    c=QuantumCircuit(2);c.barrier()
    with pytest.raises(ValueError):fuse(c)
    with pytest.raises(ValueError):fuse(QuantumCircuit(2,1))

@pytest.mark.parametrize("symbolic",[False,True])
def test_common_basis_diagnostic(symbolic):
    row=evaluate(3,8,symbolic,3)
    assert row["operator_error"]<=1e-9 and row["fused_gates"]<row["source_gates"]
