"""Numeric and decoder acceptance edges, independent small oracles."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp, Statevector

def test_symbolic_and_empty_native_observables():
    with pytest.raises(ValueError):
        q.Observable.from_qiskit(SparsePauliOp("X",coeffs=np.array([Parameter("a")],dtype=object)))
    with pytest.raises(ValueError):
        q.Observable({"":1.})
    with pytest.raises(q.ResourceLimit):
        q.Observable.from_qiskit(SparsePauliOp.from_list([("",1.)]))
    zero=q.Observable({"XY":0.}).on([3,0],width=4)
    assert zero.to_dict()=={"IIII":0.}
    np.testing.assert_array_equal(zero.to_qiskit().to_matrix(),np.zeros((16,16)))
    with pytest.raises(q.ResourceLimit):
        zero.on([0,1,2,3],width=63)

def test_pauli_product_work_and_output_caps():
    # All 64 labels over 3 wires, tensored with identities on disjoint support.
    words=["".join(x) for x in itertools.product("IXYZ",repeat=3)]
    left=q.Observable({w+"III":1. for w in words})
    right=q.Observable({"III"+w:1. for w in words})
    # 4096 pairs fit work cap but exceed 256 distinct output labels.
    with pytest.raises(q.ResourceLimit,match="output terms"):
        left.product(right)
    bigger=q.Observable({**left.to_dict(),"IIIIIX":1.})
    with pytest.raises(q.ResourceLimit,match="term pairs"):
        bigger.product(right)

def test_grouped_contract_preflight_and_limits(monkeypatch):
    r=q.Circuit(3).run()
    obs=["".join(x) for x in itertools.product("IZ",repeat=3)]
    # 32 distinct full-width terms on a 5-wire zero input.
    r=q.Circuit(5).run()
    obs=["".join(x) for x in itertools.product("IZ",repeat=5)]
    targets=dict.fromkeys(obs,1.)
    assert r.math.expectations(obs)==(1.,)*32
    assert r.verify(expectations=targets).status=="PASS"
    assert q.Contract(5,expectations=targets).verify(r).status=="PASS"
    h=q.Z(0);duplicate=q.Observable({"IIIIZ":1.})
    def forbidden(*a,**kw):pytest.fail("invalid predicates reached native evaluation")
    monkeypatch.setattr(Statevector,"expectation_value",forbidden)
    for construct in (lambda v:q.Contract(5,expectations=v),lambda v:r.verify(expectations=v)):
        with pytest.raises(ValueError,match="duplicate"):
            construct({h:1.,duplicate:1.})
        with pytest.raises(q.ResourceLimit):
            construct({**targets,"IIIIX":0.})
        with pytest.raises(ValueError):
            construct({"IIIII":1.,"bad":0.})
    with pytest.raises(q.ResourceLimit):
        r.math.expectations(obs+["IIIII"])

@pytest.mark.parametrize("n",range(2,7))
def test_simon_rank_independent_exhaustion(n):
    for secret in (1,(1<<n)-1,(1<<(n-1))|1):
        labels=[format(i,f"0{n}b") for i in range(1<<n) if (i&secret).bit_count()%2==0]
        candidates=[k for k in range(1,1<<n) if all((int(x,2)&k).bit_count()%2==0 for x in labels)]
        assert candidates==[secret]
        assert q.recover_simon(labels,n)==format(secret,f"0{n}b")
        assert q.recover_simon(reversed(labels),n)==format(secret,f"0{n}b")
    assert q.recover_simon(["0"*n]*3,n) is None
    with pytest.raises(ValueError):
        q.recover_simon([format(1<<i,f"0{n}b") for i in range(n)],n)

def test_simon_invalid_and_bounded_consumption():
    with pytest.raises(ValueError):q.recover_simon(["000","00x"],3)
    with pytest.raises(q.ResourceLimit):q.recover_simon(itertools.repeat("000"),3)
    with pytest.raises(q.ResourceLimit):q.recover_simon([],11)
