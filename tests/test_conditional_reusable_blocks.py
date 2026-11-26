"""S03 explicit reusable conditional block candidate."""
import pytest
import ketary as q
from qiskit import QuantumCircuit

@pytest.mark.parametrize("value,prepared",[(1,1),(0,0),(1,0),(0,1)])
def test_conditional_reusable_block(value,prepared):
    c=q.Circuit.classical(3,3)
    native=QuantumCircuit(3,3)
    if prepared:c.x(0);native.x(0)
    c.measure(0,0);native.measure(0,0)
    block=q.Circuit(2).x(0).cx(0,1)
    assert c.if_apply(block,bit=0,wires=[2,1],value=value) is c
    with native.if_test((native.clbits[0],value)):
        native.x(2);native.cx(2,1)
    c.measure([1,2],[1,2]);native.measure([1,2],[1,2])
    assert c.to_qiskit()==native
    block.h(1)
    assert c.to_qiskit()==native
    # Structural checks run without the optional Aer dependency.

@pytest.mark.parametrize("value,prepared",[(1,1),(0,0),(1,0),(0,1)])
def test_conditional_reusable_block_shots(value,prepared):
    pytest.importorskip("qiskit_aer")
    c=q.Circuit.classical(3,3)
    if prepared:c.x(0)
    c.measure(0,0).if_apply(q.Circuit(2).x(0).cx(0,1),bit=0,wires=[2,1],value=value).measure([1,2],[1,2])
    want=("11" if prepared==value else "00")+str(prepared)
    assert c.run_shots(shots=32,seed=7).counts=={want:32}

def test_invalid_and_resource_preflight(monkeypatch):
    c=q.Circuit.classical(3,1).measure(0,0);before=c.to_qiskit()
    p=q.Circuit.parameter("p")
    block=q.Circuit(2).h(0).cx(0,1)
    for b,kw,error in [(block,{"bit":1},ValueError),(block,{"bit":0,"wires":[1,1]},ValueError),(block,{"bit":0,"value":2},ValueError),
                      (q.Circuit.symbolic(1).rx(p,0),{"bit":0},q.UnsupportedOperation),
                      (q.Circuit.classical(1,1),{"bit":0},q.UnsupportedOperation),(object(),{"bit":0},TypeError)]:
        with pytest.raises(error):c.if_apply(b,**kw)
        assert c.to_qiskit()==before
    large=q.Circuit(1)
    for _ in range(1023):large.x(0)
    with pytest.raises(q.ResourceLimit):c.if_apply(large,bit=0,wires=[2])
    assert c.to_qiskit()==before
    original=QuantumCircuit.compose
    def fail(self,*a,**k):
        original(self,*a,**k)
        raise RuntimeError("injected branch failure")
    monkeypatch.setattr(QuantumCircuit,"compose",fail)
    with pytest.raises(RuntimeError):c.if_apply(block,bit=0,wires=[2,1])
    assert c.to_qiskit()==before
