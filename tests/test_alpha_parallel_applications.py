"""Additional distinct authored workflows, not a usability study."""
import numpy as np
import pytest
from scipy.optimize import minimize_scalar
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector
import ketary as q

def test_multi_mark_full_operator():
    marked=("001","110");N=8
    D=2*np.ones((N,N))/N-np.eye(N)
    O=np.diag([-1 if format(i,"03b") in marked else 1 for i in range(N)])
    H=np.array([[1.,1.],[1.,-1.]])/np.sqrt(2)
    ref=D@O@D@O@np.kron(np.kron(H,H),H)
    c=q.amplitude_amplification(q.phase_oracle(marked),iterations=2)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,ref,atol=1e-9,rtol=0)
    theta=np.arcsin(np.sqrt(2/N))
    assert sum(c.run().math.probability(x) for x in marked)==pytest.approx(np.sin(5*theta)**2,abs=1e-9)

def test_prepared_state_reflection():
    v=np.array([1,.4j,-.2,.3+.1j]);v/=np.linalg.norm(v)
    prep=q.Circuit.prepare_state(v,seed=1101)
    np.testing.assert_allclose(prep.run().math.statevector(),v,atol=1e-9,rtol=0)
    c=q.Circuit(2).apply(prep.inverse()).apply(q.phase_oracle("00")).apply(prep)
    expected=np.eye(4)-2*np.outer(v,v.conj())
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    native=QuantumCircuit(2);native.append(prep.to_qiskit().inverse(),[0,1])
    native.x([0,1]);native.cz(0,1);native.x([0,1]);native.append(prep.to_qiskit(),[0,1])
    np.testing.assert_allclose(Operator(native).data,expected,atol=1e-9,rtol=0)

def test_controlled_prepared_reflection():
    v=np.array([1,1j])/np.sqrt(2)
    R=np.eye(2)-2*np.outer(v,v.conj())
    c=q.Circuit.from_unitary(R,seed=1101).evolve(q.I(),time=.37)
    actual=Operator(c.control(control_state=0,seed=1101).to_qiskit()).data
    expected=np.eye(4,dtype=complex)
    expected[np.ix_([0,2],[0,2])]=np.exp(-.37j)*R
    np.testing.assert_allclose(actual,expected,atol=1e-9,rtol=0)

def test_variational_overlap():
    target=.73
    v=np.array([np.cos(target/2),0,0,np.sin(target/2)],complex)
    p=q.Circuit.parameter("theta")
    template=q.Circuit.symbolic(2).ry(p,0).cx(0,1)
    histories={"sdk":[],"native":[]}
    def cost(t,route):
        if route=="sdk":state=template.bind({p:float(t)}).run().math.statevector()
        else:
            native=QuantumCircuit(2);native.ry(t,0);native.cx(0,1)
            state=Statevector.from_instruction(native).data
        loss=1-abs(np.vdot(v,state))**2
        assert loss==pytest.approx(np.sin((t-target)/2)**2,abs=1e-9)
        histories[route].append(float(loss))
        return loss
    for route in histories:
        opt=minimize_scalar(lambda t:cost(t,route),bounds=(-1.,2.),method="bounded")
        assert opt.success and opt.fun<1e-8 and len(histories[route])>2

def test_multi_observable_objective():
    p=q.Circuit.parameter("theta");c=q.Circuit.symbolic(1).ry(p,0)
    a,b=.4,.7
    history=[]
    def objective(t):
        r=c.bind({p:float(t)}).run()
        x,z=r.math.expectation(q.X(0)),r.math.expectation(q.Z(0))
        native=QuantumCircuit(1);native.ry(t,0)
        v=Statevector.from_instruction(native).data
        nx=2*np.real(v[0].conj()*v[1]);nz=abs(v[0])**2-abs(v[1])**2
        np.testing.assert_allclose([x,z],[nx,nz],atol=1e-9,rtol=0)
        loss=(x-a)**2+(z-b)**2;history.append(float(loss));return loss
    opt=minimize_scalar(objective,bounds=(0,np.pi/2),method="bounded")
    assert opt.success and len(history)>2
    assert opt.fun==pytest.approx((1-np.hypot(a,b))**2,abs=1e-9)

def test_reversible_block_verification():
    c=q.Circuit(3).ccx(0,1,2).cx(2,0)
    correct=c.copy().apply(c.inverse())
    reference=q.Circuit(3)
    correct.test.equivalent(reference).require()
    broken=correct.copy().z(1)
    assert broken.test.compare(reference,inputs=["000"]).status=="PASS"
    assert broken.test.compare(reference,inputs=["+++"]).status=="FAIL"
    report=broken.test.compare(reference,inputs=["+++"],complete=False)
    assert report.evidence.reproduce()["reproduced"]
    expected=np.diag([(-1)**((i>>1)&1) for i in range(8)])
    np.testing.assert_allclose(Operator(q.Circuit.from_json(broken.to_json()).to_qiskit()).data,expected,atol=1e-9,rtol=0)

def test_symbolic_reused_layer_reversed_wires():
    p=q.Circuit.parameter("p");layer=q.Circuit.symbolic(2).ry(p,0).cx(0,1)
    c=q.Circuit.symbolic(3).apply(layer,wires=[2,0],times=2)
    for t in (.17,-.43,.89):
        raw=QuantumCircuit(3)
        for _ in range(2):raw.ry(t,2);raw.cx(2,0)
        np.testing.assert_allclose(Operator(c.bind({p:t}).to_qiskit()).data,Operator(raw).data,atol=1e-9,rtol=0)
