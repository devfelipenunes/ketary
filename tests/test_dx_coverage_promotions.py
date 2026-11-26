import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import StatePreparation,UnitaryGate,XXPlusYYGate
from qiskit.quantum_info import Operator
from scipy.linalg import expm

def strict(a,b):
    np.testing.assert_allclose(Operator(a.to_qiskit() if isinstance(a,q.Circuit) else a).data,
                               Operator(b.to_qiskit() if isinstance(b,q.Circuit) else b).data,rtol=0,atol=1e-9)

@pytest.mark.parametrize("v",[.2,-.7,.9])
def test_symbolic_import_partial_binding(v):
    a,b=Parameter("a"),Parameter("b")
    raw=QuantumCircuit(2);raw.ry(a*b,0);raw.cx(0,1);raw.rz(b,1);raw.global_phase=a-b
    c=q.Circuit.from_symbolic(raw)
    part=c.bind_partial({a:v})
    assert part.parameters==(b,) and c.parameters==(a,b)
    with pytest.raises(q.UnsupportedOperation):part.run()
    strict(part.bind({b:.5}),raw.assign_parameters({a:v,b:.5}))
    strict(c.bind_partial({a:v,b:.5}),raw.assign_parameters({a:v,b:.5}))
    raw.x(0);assert len(c.to_qiskit().data)==3
    with pytest.raises(ValueError):c.bind_partial({Parameter("a"):v})
    with pytest.raises(ValueError):c.bind_partial({a:float("nan")})

@pytest.mark.parametrize("gate",[StatePreparation([.5,.5j,.5,-.5j]),UnitaryGate([[0,1j],[1j,0]]),XXPlusYYGate(.4,.2)])
def test_synthesis(gate):
    raw=QuantumCircuit(gate.num_qubits);raw.append(gate,range(gate.num_qubits));raw.global_phase=.31
    c=q.Circuit.from_synthesized(raw);strict(c,raw)
    assert set(item.operation.name for item in c.to_qiskit().data)<={"u","cx"}
    raw.x(0);assert not np.allclose(Operator(c.to_qiskit()).data,Operator(raw).data)

@pytest.mark.parametrize("controls,state",[(1,0),(1,1),(2,0),(2,1),(2,2),(2,3)])
def test_control_phase(controls,state):
    raw=QuantumCircuit(2);raw.ry(.4,0);raw.cx(0,1);raw.global_phase=.37
    source=q.from_qiskit(raw)
    c=source.control(controls=controls,control_state=state)
    expected=QuantumCircuit(controls+2);expected.append(raw.to_gate().control(controls,ctrl_state=state,annotated=False),range(controls+2))
    strict(c,expected);strict(source,raw)

def test_synthesis_rejections():
    c=QuantumCircuit(1);c.barrier()
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_synthesized(c)
    with pytest.raises(q.ResourceLimit):q.Circuit.from_synthesized(QuantumCircuit(6))
    c=QuantumCircuit(1);c.metadata={"a":1}
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_synthesized(c)
    with pytest.raises(ValueError):q.bell().control(control_state=2)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.symbolic(1).ry(q.Circuit.parameter("x"),0).control()

@pytest.mark.parametrize("order",[1,2])
@pytest.mark.parametrize("t",[.4,-.7])
def test_product_formula(order,t):
    H=q.X(0)+.7*q.Z(0)+.3
    x=np.array([[0,1],[1,0]],complex);z=np.diag([1.,-1.]);I=np.eye(2)
    want=expm(-1j*t*(x+.7*z+.3*I))
    errors=[]
    for steps in (1,4,16):
        terms=[.3*I,x,.7*z];seq=terms if order==1 else terms+terms[::-1]
        step=I.astype(complex)
        for P in seq:step=expm(-1j*t/(steps*order)*P)@step
        got=Operator(q.Circuit(1).evolve_product(H,time=t,steps=steps,order=order).to_qiskit()).data
        np.testing.assert_allclose(got,np.linalg.matrix_power(step,steps),atol=1e-9,rtol=0)
        errors.append(np.linalg.norm(got-want))
    assert errors[2]<errors[1]<errors[0]

def test_product_formula_rollback():
    c=q.bell();before=c.to_qiskit()
    for kw in (dict(time=.3,steps=0),dict(time=.3,steps=65),dict(time=.3,steps=1,order=3),dict(time=float("nan"),steps=1)):
        with pytest.raises(ValueError):c.evolve_product(q.X(0)+q.Z(0),**kw)
        assert c.to_qiskit()==before
    with pytest.raises(q.UnsupportedOperation):c.evolve(q.X(0)+q.Z(0),time=.2)

@pytest.mark.parametrize("a",["I","X","Y","Z"])
@pytest.mark.parametrize("b",["I","X","Y","Z"])
def test_pauli_algebra(a,b):
    mats={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    A=q.Observable({a:1.});B=q.Observable({b:1.});x,y=mats[a],mats[b]
    np.testing.assert_allclose(A.product(B).to_matrix(),x@y,rtol=0,atol=1e-12)
    np.testing.assert_allclose(A.commutator(B).to_matrix(),x@y-y@x,rtol=0,atol=1e-12)
    np.testing.assert_allclose(A.anticommutator(B).to_qiskit().to_matrix(),x@y+y@x,rtol=0,atol=1e-12)

def test_multiterm_algebra():
    A=q.X(0)+.3*q.Y(1);B=q.Z(0)+.8*q.X(1)
    x=A.to_qiskit(2).to_matrix();y=B.to_qiskit(2).to_matrix()
    np.testing.assert_allclose(A.product(B).to_matrix(),x@y,atol=1e-12,rtol=0)
    np.testing.assert_allclose(A.commutator(B).to_matrix(),x@y-y@x,atol=1e-12,rtol=0)
    np.testing.assert_allclose(A.anticommutator(B).to_qiskit().to_matrix(),x@y+y@x,atol=1e-12,rtol=0)
