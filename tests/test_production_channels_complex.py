import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Kraus,DensityMatrix,SparsePauliOp

@pytest.mark.parametrize("gamma",[0.,.001,.2,.7,1.])
@pytest.mark.parametrize("mixed",[False,True])
def test_amplitude_damping_oracle(gamma,mixed):
    K0=np.diag([1.,np.sqrt(1-gamma)])
    K1=np.array([[0,np.sqrt(gamma)],[0,0]])
    rho=np.array([[.6,.1j],[-.1j,.4]]) if mixed else np.array([[1.,0],[0,0]])
    initial=DensityMatrix(rho) if mixed else None
    X=np.array([[0,1],[1,0]])
    expected=sum(K@X@rho@X@K.conj().T for K in (K0,K1))
    out=q.Circuit(1).x(0).run_channel(Kraus([K0,K1]),initial)
    np.testing.assert_allclose(out.data,expected,atol=1e-9,rtol=0)
    assert out.is_valid()
    if initial is not None:np.testing.assert_array_equal(initial.data,rho)

@pytest.mark.parametrize("p",[0.,.1,.5,1.])
def test_entangled_dephasing_oracle(p):
    I=np.eye(4)
    Z=np.kron(np.eye(2),np.diag([1,-1]))
    v=np.array([1,0,0,1])/np.sqrt(2)
    rho=np.outer(v,v)
    out=q.bell().run_channel(Kraus([np.sqrt(1-p)*I,np.sqrt(p)*Z]))
    np.testing.assert_allclose(out.data,(1-p)*rho+p*Z@rho@Z,atol=1e-9,rtol=0)

def test_channel_rejects_before_execution(monkeypatch):
    from qiskit.quantum_info import DensityMatrix
    c=q.Circuit(1)
    monkeypatch.setattr(DensityMatrix,"from_instruction",lambda *a,**kw:pytest.fail("hidden execution before preflight"))
    for channel,exc in [(object(),TypeError),(Kraus([np.eye(4)]),ValueError),(Kraus([np.eye(2)*.5]),ValueError)]:
        with pytest.raises(exc):c.run_channel(channel)
    with pytest.raises(q.ResourceLimit):c.run_channel(Kraus([np.eye(2)]),max_bytes=255)
    with pytest.raises(q.ResourceLimit):q.Circuit(5).run_channel(Kraus([np.eye(2)]))

@pytest.mark.parametrize("n",[1,2,3,4])
@pytest.mark.parametrize("seed",range(6))
def test_complex_pauli_expectation(n,seed):
    rng=np.random.default_rng(seed+733)
    v=rng.normal(size=2**n)+1j*rng.normal(size=2**n);v/=np.linalg.norm(v)
    paulis={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    terms=[];matrix=np.zeros((2**n,2**n),complex)
    for _ in range(7):
        label="".join(rng.choice(list(paulis),size=n))
        coefficient=complex(rng.normal(),rng.normal())
        M=np.ones((1,1),complex)
        for p in label:M=np.kron(M,paulis[p])
        matrix+=coefficient*M
        terms.append((label,coefficient))
    got=q.Result(v).math.expectation_complex(SparsePauliOp.from_list(terms))
    np.testing.assert_allclose(got,np.vdot(v,matrix@v),atol=1e-9,rtol=0)

def test_complex_expectation_preflight_and_cancellation(monkeypatch):
    r=q.bell().run()
    with pytest.raises(TypeError):r.math.expectation_complex("XX")
    with pytest.raises(ValueError):r.math.expectation_complex(SparsePauliOp("X"))
    with pytest.raises(q.ResourceLimit):r.math.expectation_complex(SparsePauliOp.from_list([("XX",1)]*257))
    with pytest.raises(q.ResourceLimit):r.math.expectation_complex(SparsePauliOp("XX"),max_work=3)
    # Opposite large coefficients must not lose the small middle term.
    op=SparsePauliOp.from_list([("XX",1e16+1e16j),("XX",1+2j),("XX",-1e16-1e16j)])
    np.testing.assert_allclose(r.math.expectation_complex(op),1+2j,atol=1e-9,rtol=0)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**kw:pytest.fail("implicit simulation"))
    assert r.math.expectation_complex(SparsePauliOp.from_list([("XX",1j)]))==pytest.approx(1j)
