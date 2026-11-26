"""Deutsch-Jozsa oracle and marginal semantics against independent fixtures."""
import itertools
import numpy as np
import pytest
from qiskit.quantum_info import Operator
import ketary as q

@pytest.mark.parametrize("n",[1,2,3,4])
@pytest.mark.parametrize("value",[0,1])
def test_constant(n,value):
    oracle=q.constant_oracle(n,value=value)
    c=q.deutsch_jozsa(oracle)
    assert type(c) is q.Circuit
    p=c.run().math.marginal_probabilities(range(n-1,-1,-1))
    assert p["0"*n]==pytest.approx(1)
    assert sum(p.values())==pytest.approx(1)

@pytest.mark.parametrize("mask",["1","01","10","11","101","111","0010"])
@pytest.mark.parametrize("offset",[0,1])
def test_parity(mask,offset):
    oracle=q.parity_oracle(mask,offset=offset)
    n=len(mask)
    p=q.deutsch_jozsa(oracle).run().math.marginal_probabilities(range(n-1,-1,-1))
    assert p[mask]==pytest.approx(1)
    assert p["0"*n]==pytest.approx(0,abs=1e-12)
    # Verify full bit-flip oracle, including the y=1 input.
    expected=np.zeros((2**(n+1),2**(n+1)),complex)
    for x in range(2**n):
        f=((x&int(mask,2)).bit_count()%2)^offset
        for y in (0,1):
            expected[x+((y^f)<<n),x+(y<<n)]=1
    np.testing.assert_allclose(Operator(oracle.to_qiskit()).data,expected,atol=1e-12)

def test_nonlinear_balanced_explicit_oracle():
    # f(x)=x2 XOR (x0 AND x1) is balanced but not affine.
    o=q.Circuit(4).gates.ccx(0,1,3).gates.cx(2,3)
    before=o.to_qiskit()
    c=q.deutsch_jozsa(o)
    p=c.run().math.marginal_probabilities([2,1,0])
    for k in range(8):
        amplitude=sum((-1)**(((x>>2)^((x&1)*((x>>1)&1)))%2+(x&k).bit_count()) for x in range(8))/8
        assert p[format(k,"03b")]==pytest.approx(amplitude**2,abs=1e-12)
    assert p["000"]==pytest.approx(0,abs=1e-12)
    c.gates.z(0)
    assert o.to_qiskit()==before

def test_marginal_order_and_no_execution(monkeypatch):
    r=q.Circuit(3).gates.x(2).run()
    def fail(*a,**k): raise AssertionError("unexpected execution")
    monkeypatch.setattr(q.Circuit,"run",fail)
    assert r.math.marginal_probabilities([2,0])["10"]==1
    assert r.math.marginal_probabilities([0,2])["01"]==1
    assert r.math.marginal_probabilities([1])["0"]==1

@pytest.mark.parametrize("wires",[[],[0,0],[3],[-1],[True],[.5]])
def test_bad_marginal(wires):
    with pytest.raises(ValueError): q.ghz(3).run().math.marginal_probabilities(wires)

@pytest.mark.parametrize("mask",["","000","12",None])
def test_bad_mask(mask):
    with pytest.raises(ValueError): q.parity_oracle(mask)

def test_invalid_oracles():
    with pytest.raises(TypeError): q.deutsch_jozsa(None)
    with pytest.raises(ValueError): q.deutsch_jozsa(q.Circuit(1))
    with pytest.raises(ValueError): q.constant_oracle(2,value=2)
    with pytest.raises(ValueError): q.parity_oracle("1",offset=-1)
