"""Explicit structural handoff and ideal-only projection."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit,QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit import Barrier

@pytest.mark.parametrize("wires",[[0],[1],[0,1],[1,0]])
def test_annotated_projection_structural_and_math(wires):
    raw=QuantumCircuit(QuantumRegister(2,"lab"),name="experiment",metadata={"calibration":{"versions":[1,2]},"flag":True,"scale":.2})
    raw.h(0);raw.barrier(*wires);raw.cx(0,1);raw.global_phase=.37
    logical,native=q.Circuit.project_annotated(raw)
    assert native==raw and native.name=="experiment"
    assert [(reg.name,len(reg)) for reg in native.qregs]==[("lab",2)]
    assert [i.operation.name for i in native.data]==["h","barrier","cx"]
    assert [native.find_bit(w).index for w in native.data[1].qubits]==wires
    assert native.metadata==raw.metadata
    assert logical.to_qiskit().metadata=={}
    assert [i.operation.name for i in logical.to_qiskit().data]==["h","cx"]
    np.testing.assert_allclose(Operator(logical.to_qiskit()).data,Operator(raw).data,atol=1e-9,rtol=0)
    raw.metadata["calibration"]["versions"].append(3)
    assert native.metadata["calibration"]["versions"]==[1,2]
    native.metadata["calibration"]["versions"].append(4)
    assert raw.metadata["calibration"]["versions"]==[1,2,3]
    logical.x(0)
    assert len(native.data)==3
    native.z(1)
    assert [i.operation.name for i in logical.to_qiskit().data]==["h","cx","x"]
    with pytest.raises(q.UnsupportedOperation):q.from_qiskit(raw)

@pytest.mark.parametrize("metadata",[
    {"bad":float("nan")},{"bad":float("inf")},{"bad":object()},
    {1:"not string"},{"bad":(1,2)},{"bad":complex(1,2)},{"bad":"\ud800"}])
def test_bad_metadata_rejected_before_copy(metadata,monkeypatch):
    raw=QuantumCircuit(1,metadata=metadata)
    monkeypatch.setattr(QuantumCircuit,"copy",lambda *a,**k:pytest.fail("copy before validation"))
    with pytest.raises(ValueError):q.Circuit.project_annotated(raw)

@pytest.mark.parametrize("kind",["cycle","deep","nodes","string","bytes","integer"])
def test_metadata_budgets(kind,monkeypatch):
    if kind=="cycle":
        metadata={};metadata["loop"]=metadata
    elif kind=="deep":
        value=0
        for _ in range(10):value=[value]
        metadata={"deep":value}
    elif kind=="nodes":metadata={"nodes":[0]*4096}
    elif kind=="string":metadata={"s":"x"*4097}
    elif kind=="bytes":metadata={str(i):"é"*4096 for i in range(9)}
    else:metadata={"integer":1<<65}
    raw=QuantumCircuit(1)
    raw.metadata=metadata
    monkeypatch.setattr(QuantumCircuit,"copy",lambda *a,**k:pytest.fail("copy before validation"))
    with pytest.raises(q.ResourceLimit):q.Circuit.project_annotated(raw)

@pytest.mark.parametrize("kind",["measure","reset","unbound","custom"])
def test_annotated_unsupported_never_projected(kind):
    if kind=="measure":
        raw=QuantumCircuit(1,1);raw.measure(0,0)
    else:
        raw=QuantumCircuit(1)
        if kind=="reset":raw.reset(0)
        elif kind=="unbound":raw.ry(q.Circuit.parameter("t"),0)
        else:
            g=QuantumCircuit(1);g.h(0);raw.append(g.to_gate(),[0])
    with pytest.raises(q.UnsupportedOperation):q.Circuit.project_annotated(raw)

def test_projection_does_not_claim_barrier_equivalence():
    raw=QuantumCircuit(1,metadata={"experiment":"fence"});raw.h(0);raw.barrier();raw.h(0)
    logical,native=q.Circuit.project_annotated(raw)
    assert len(logical.optimize().to_qiskit().data)==0
    assert [i.operation.name for i in native.data]==["h","barrier","h"]
    assert native.metadata=={"experiment":"fence"}
    np.testing.assert_allclose(logical.run().math.statevector(),[1,0],atol=1e-9)
