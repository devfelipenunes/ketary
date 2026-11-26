"""Independent qualification of product formulas and differential geometry.

These are research oracles, not public Hessian/QGT APIs or formal certificates.
"""
import numpy as np
import pytest
from scipy.linalg import expm
from qiskit.quantum_info import Operator
import ketary as q

@pytest.mark.parametrize("theta",[-2.4,-.8,0.,.2,1.1,2.7])
@pytest.mark.parametrize("phi",[-1.3,.4,2.1])
def test_hessian_and_geometry(theta,phi):
    a,b=q.Circuit.parameter_vector("v",2)
    c=q.Circuit.symbolic(1).ry(a,0).rz(b,0)
    bindings={a:theta,b:phi}
    obs=[q.X(0),q.Y(0),q.Z(0)]
    # F(theta,phi)=(sin(theta)cos(phi),sin(theta)sin(phi),cos(theta)).
    s,t=np.sin(theta),np.cos(theta)
    u,v=np.sin(phi),np.cos(phi)
    expected=np.array([[t*v,-s*u],[t*u,s*v],[-s,0.]])
    np.testing.assert_allclose(c.expectation_jacobian(bindings,obs),expected,atol=1e-9,rtol=0)
    h=1e-4
    hess=[]
    for p in (a,b):
        left=dict(bindings);right=dict(bindings);left[p]+=h;right[p]-=h
        hess.append((np.array(c.expectation_jacobian(left,obs))-np.array(c.expectation_jacobian(right,obs)))/(2*h))
    got=np.stack(hess,axis=2)
    want=np.array([[[-s*v,-t*u],[-t*u,-s*v]],[[-s*u,t*v],[t*v,-s*u]],[[-t,0],[0,0]]])
    np.testing.assert_allclose(got,want,atol=1e-7,rtol=0)
    np.testing.assert_allclose(got,np.swapaxes(got,1,2),atol=1e-7,rtol=0)
    psi=c.bind(bindings).run().math.statevector()
    # Exact occurrence-wise derivative for a single Pauli rotation per parameter.
    columns=[]
    for p in (a,b):
        left=dict(bindings);right=dict(bindings);left[p]+=np.pi/2;right[p]-=np.pi/2
        columns.append((c.bind(left).run().math.statevector()-c.bind(right).run().math.statevector())/(2*np.sqrt(2)))
    D=np.column_stack(columns)
    Q=D.conj().T@(np.eye(2)-np.outer(psi,psi.conj()))@D
    # Our coordinate/gauge choice fixes the sign of Im Q_theta,phi.
    expected_Q=np.array([[1,1j*s],[-1j*s,s*s]],complex)/4
    np.testing.assert_allclose(Q,expected_Q,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Q,Q.conj().T,atol=1e-9,rtol=0)
    assert np.linalg.eigvalsh(Q).min()>=-1e-9
    gauge=np.exp(.73j);dg=np.array([.4,-.9])
    Dg=gauge*(D+1j*np.outer(psi,dg));pg=gauge*psi
    np.testing.assert_allclose(Dg.conj().T@(np.eye(2)-np.outer(pg,pg.conj()))@Dg,Q,atol=1e-9,rtol=0)

@pytest.mark.parametrize("n",[1,2,3])
@pytest.mark.parametrize("seed",range(12))
def test_lie_product_error_bound(n,seed):
    rng=np.random.default_rng(seed+631)
    X=np.array([[0,1],[1,0]],complex);Z=np.diag([1,-1])
    I=np.eye(2**n)
    A=np.kron(np.eye(2**(n-1)),X)
    B=np.kron(np.eye(2**(n-1)),Z)
    a,b=rng.uniform(.2,1.2,size=2);t=rng.uniform(.1,.6)
    H=a*q.X(0)+b*q.Z(0)
    exact=expm(-1j*t*(a*A+b*B))
    errors=[]
    comm=np.linalg.norm((a*A)@(b*B)-(b*B)@(a*A),ord=2)
    for steps in [1,2,4,8]:
        first=Operator(q.Circuit(n).evolve_product(H,time=t,steps=steps,order=1).to_qiskit()).data
        second=Operator(q.Circuit(n).evolve_product(H,time=t,steps=steps,order=2).to_qiskit()).data
        e1=np.linalg.norm(first-exact,ord=2)
        e2=np.linalg.norm(second-exact,ord=2)
        assert e1<=t*t*comm/(2*steps)+1e-9
        assert e2<=e1+1e-9
        errors.append(e2)
        np.testing.assert_allclose(second.conj().T@second,I,atol=1e-9,rtol=0)
    assert errors[-1]<errors[0]

@pytest.mark.parametrize("seed",range(60))
def test_random_reversible_circuit_oracle(seed):
    rng=np.random.default_rng(seed+789)
    n=int(rng.integers(1,5))
    c=q.Circuit(n)
    # Independently track basis-label permutation and complex phase.
    permutation=np.arange(2**n);phase=np.ones(2**n,complex)
    for _ in range(30):
        w=int(rng.integers(n));gate=int(rng.integers(4))
        if gate==0:
            c.x(w);permutation^=1<<w
        elif gate==1:
            c.z(w);phase*=1-2*((permutation>>w)&1)
        elif gate==2:
            angle=float(rng.uniform(-np.pi,np.pi))
            c.p(angle,w);phase*=np.exp(1j*angle*((permutation>>w)&1))
        elif n>1:
            target=(w+1)%n;c.cx(w,target)
            permutation^=((permutation>>w)&1)<<target
    expected=np.zeros((2**n,2**n),complex)
    expected[permutation,np.arange(2**n)]=phase
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(c.inverse().to_qiskit()).data,expected.conj().T,atol=1e-9,rtol=0)
