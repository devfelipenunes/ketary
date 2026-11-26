"""Builtin fluent dispatch must retain the validated scalar and batch paths."""
import numpy as np
import pytest
import ketary as q
from fractions import Fraction
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("name",["h","x","y","z","s","sdg","t","tdg","sx","sxdg","rx","ry","rz","p","u"])
@pytest.mark.parametrize("wire",[0,np.int64(1),range(2)])
def test_scalar_and_batch_dispatch(name,wire):
    args=(.37,-.19,.7) if name=="u" else (.37,) if name in ("rx","ry","rz","p") else ()
    c=q.Circuit(2)
    raw=QuantumCircuit(2)
    getattr(raw,name)(*args,list(wire) if isinstance(wire,range) else int(wire))
    assert getattr(c,name)(*args,wire) is c
    assert c.to_qiskit()==raw
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(raw).data,atol=1e-9,rtol=0)

@pytest.mark.parametrize("name",["rx","ry","rz","p"])
@pytest.mark.parametrize("angle",[1,0.,-0.,Fraction(1,3),np.float64(.2)])
def test_numeric_angle_and_symbolic_dispatch(name,angle):
    c=q.Circuit(2)
    raw=QuantumCircuit(2)
    getattr(raw,name)(float(angle),1)
    getattr(c,name)(angle,1)
    assert c.to_qiskit()==raw
    p=q.Circuit.parameter("p")
    symbolic=q.Circuit.symbolic(2)
    getattr(symbolic,name)(p,1)
    assert symbolic.bind({p:float(angle)}).to_qiskit()==raw

@pytest.mark.parametrize("name",["h","rx","u"])
@pytest.mark.parametrize("wire",[True,-1,2,1.2])
def test_invalid_wire_atomicity(name,wire):
    args=(.1,.2,.3) if name=="u" else (.1,) if name=="rx" else ()
    c=q.Circuit(2).h(0).checkpoint("start")
    before=c.to_qiskit()
    with pytest.raises((ValueError,TypeError)):
        getattr(c,name)(*args,wire)
    assert c.to_qiskit()==before and c.checkpoints=={"start":1}

@pytest.mark.parametrize("angle",[True,float("nan"),float("inf"),2**10000])
def test_invalid_scalar_angle_atomicity(angle):
    c=q.Circuit(2).h(0)
    before=c.to_qiskit()
    with pytest.raises(ValueError):c.ry(angle,0)
    assert c.to_qiskit()==before
