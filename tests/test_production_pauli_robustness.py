"""Cancellation and bounded randomized Pauli algebra: independent dense oracles."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import SparsePauliOp

@pytest.mark.parametrize("order",list(itertools.permutations([1e16,1.,-1e16])))
def test_duplicate_real_cancellation(order):
    op=SparsePauliOp.from_list([("X",v) for v in order])
    assert q.Observable.from_qiskit(op).to_dict()=={"X":1.}
    assert q.Circuit(1).h(0).run().math.expectation(q.Observable.from_qiskit(op))==pytest.approx(1.)

@pytest.mark.parametrize("order",list(itertools.permutations([1e16j,1j,-1e16j])))
def test_duplicate_imaginary_residual_rejected(order):
    with pytest.raises(ValueError,match="real aggregate"):
        q.Observable.from_qiskit(SparsePauliOp.from_list([("X",v) for v in order]))

def test_product_cancellation_identity():
    a=q.Observable({"I":1e16,"X":1.,"Y":-1e16})
    b=q.Observable({"I":1.,"X":1.,"Y":1.})
    assert dict(a.product(b).to_list())["I"]==1.
    assert a.anticommutator(b).to_dict()["I"]==2.

def test_overflow_not_silently_accepted():
    with pytest.raises(ValueError):q.Observable.from_qiskit(SparsePauliOp.from_list([("X",1e308),("X",1e308)]))
    with pytest.raises(ValueError):q.Observable({"I":1e308}).product(q.Observable({"I":1e308}))

def test_exact_imaginary_cancellation():
    op=SparsePauliOp.from_list([("Y",1e16j),("Y",.25),("Y",-1e16j)])
    assert q.Observable.from_qiskit(op).to_dict()=={"Y":.25}

@pytest.mark.parametrize("n",[1,2,3,4])
@pytest.mark.parametrize("seed",range(16))
def test_pauli_algebra_dense_oracle(n,seed):
    rng=np.random.default_rng(881+seed)
    mats={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1.,-1.])}
    def build():
        terms={}
        for _ in range(8):
            p="".join(rng.choice(list(mats),n))
            terms[p]=float(rng.uniform(-2,2))
        matrix=np.zeros((2**n,2**n),complex)
        for p,v in terms.items():
            m=np.ones((1,1),complex)
            for s in p:m=np.kron(m,mats[s])
            matrix+=v*m
        return q.Observable(terms),matrix
    A,a=build();B,b=build()
    np.testing.assert_allclose(A.product(B).to_matrix(),a@b,atol=1e-9,rtol=0)
    np.testing.assert_allclose(A.commutator(B).to_matrix(),a@b-b@a,atol=1e-9,rtol=0)
    np.testing.assert_allclose(A.anticommutator(B).to_qiskit().to_matrix(),a@b+b@a,atol=1e-9,rtol=0)
    # For Hermitian inputs, (AB)^dagger=BA and [A,B]^dagger=-[A,B].
    np.testing.assert_allclose(A.product(B).to_matrix().conj().T,B.product(A).to_matrix(),atol=1e-9,rtol=0)
    np.testing.assert_allclose(A.commutator(B).to_matrix().conj().T,-A.commutator(B).to_matrix(),atol=1e-9,rtol=0)
