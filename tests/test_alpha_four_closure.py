"""Closure checks for #105 #154 #303 #109; no runtime promotion."""
import numpy as np
import pytest
import ketary as q
from scipy.linalg import expm
from qiskit.quantum_info import Operator
from research.alpha_api_usage import inventory
from research.alpha_four_parity import coherent,dense,symbolic_shared
from research.alpha_mixed_parity import fixture,shared
from research.alpha_four_verification import grouped,checkpoint,replay

def test_api_usage_inventory():
    r=inventory()
    assert r["categories"]=={"Core":94,"Advanced":182,"Native":20,"Compatibility":34}
    assert len(r["rows"])==len({x["symbol"] for x in r["rows"]})==330
    assert r["files"]>0
    rows={x["symbol"]:x for x in r["rows"]}
    assert rows["Circuit"]["direct_syntactic_references"]>0
    assert rows["Circuit.apply"]["stub_declarations"]
    assert rows["_Math.expectations"]["stub_declarations"]
    assert all(x["lifecycle"]["category"]==x["category"] for x in r["rows"])

def test_coherent_parity_and_measured_scope():
    r=coherent()
    assert r["coherent_off_diagonal"]==pytest.approx(.5)
    assert r["nonselective_measured_off_diagonal"]==0

@pytest.mark.parametrize("seed",[1101,2202,3303])
@pytest.mark.parametrize("n",[4,5,6])
def test_symbolic_shared_basis(seed,n):
    terms=fixture(n,seed);p=q.Circuit.parameter("t")
    c=symbolic_shared(n,terms,p)
    for t in (-.41,0.,.37):
        expected=expm(-1j*t*dense(terms))
        for actual in (c.bind({p:t}),shared(n,terms,t)):
            np.testing.assert_allclose(Operator(actual.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    assert c.parameters==(p,)

def test_shared_basis_rejects_incompatible_local_axes():
    terms={"XX":.4,"ZZ":.7}
    # These commute globally, but are not diagonalizable in one shared local basis.
    with pytest.raises(ValueError):shared(2,terms,.3)
    with pytest.raises(ValueError):symbolic_shared(2,terms,q.Circuit.parameter("t"))
    np.testing.assert_allclose(Operator(q.Circuit(2).evolve(q.Observable(terms),time=.3).to_qiskit()).data,expm(-.3j*dense(terms)),atol=1e-9,rtol=0)

@pytest.mark.parametrize("factory,routes",[(grouped,("grouped","scalar")),(checkpoint,("grouped","scalar")),(replay,("typed","direct"))])
def test_matched_verification_profiles(factory,routes):
    for route in routes:
        run,check,_=factory(4,route)
        check(run())
