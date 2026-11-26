"""Bounded independent dense oracles for ordered product-formula error.

Refs #286 #287 #316 #254. Research evidence, not a public error estimator.
"""
import itertools
import numpy as np
import pytest
from scipy.linalg import expm
from qiskit.quantum_info import Operator
import ketary as q

_PAULI={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),
        "Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}

def _matrix(label):
    out=np.ones((1,1),complex)
    for s in label:
        out=np.kron(out,_PAULI[s])
    return out

def _comm(a,b):
    return a@b-b@a

def _norm(a):
    return float(np.linalg.norm(a,2))

def _bounds(mats,t,r):
    # Hermitian, time-independent ordered terms; spectral norm.
    c1=c2=0.
    for i,a in enumerate(mats):
        b=sum(mats[i+1:],np.zeros_like(a))
        ab=_comm(a,b)
        c1+=_norm(ab)/2
        c2+=_norm(_comm(a,ab))/24+_norm(_comm(b,ab))/12
    return min(2.,c1*t*t/r),min(2.,c2*abs(t)**3/r**2)

@pytest.mark.parametrize("seed",range(32))
@pytest.mark.parametrize("order",[1,2])
def test_seeded_multiterm_commutator_bound(seed,order):
    rng=np.random.default_rng(93200+seed)
    n=2+seed%2
    labels=["".join(x) for x in itertools.product("IXYZ",repeat=n)]
    terms=dict(sorted(zip(rng.choice(labels,size=4,replace=False),
                          rng.uniform(-1,1,4))))
    terms={str(k):float(v) for k,v in terms.items()}
    mats=[v*_matrix(k) for k,v in terms.items()]
    t=float(rng.uniform(-1.3,1.3))
    exact=expm(-1j*t*sum(mats))
    for r in (1,4,16):
        seq=mats if order==1 else mats+mats[::-1]
        step=np.eye(2**n,dtype=complex)
        for a in seq:
            step=expm(-1j*t/(r*order)*a)@step
        dense=np.linalg.matrix_power(step,r)
        bound=_bounds(mats,t,r)[order-1]
        assert _norm(dense-exact)<=bound+2e-12
        native=Operator(q.Circuit(n).evolve_product(q.Observable(terms),
                        time=t,steps=r,order=order).to_qiskit()).data
        # Distinguish product-formula approximation from implementation error.
        np.testing.assert_allclose(native,dense,atol=1e-9,rtol=0)
        assert _norm(native-exact)<=bound+2**n*1e-9+2e-12

def test_commuting_and_identity_terms_zero_bound():
    terms=[.3*_matrix("II"),.8*_matrix("ZI"),-.4*_matrix("ZZ")]
    assert _bounds(terms,.4,8)==(0.,0.)
    assert _bounds(terms,0.,1)==(0.,0.)

def test_wrong_sign_detected_even_with_zero_bound():
    m=_matrix("XZ")
    t=.37
    assert _bounds([m],t,4)==(0.,0.)
    assert _norm(expm(1j*t*m)-expm(-1j*t*m))>.5
