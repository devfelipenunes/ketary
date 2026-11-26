import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Statevector
from research.pauli_query_attribution import evaluate,_query,workload,independent

@pytest.mark.parametrize("n,count",[(4,1),(4,8),(8,8),(8,32)])
def test_attribution_correctness(n,count):
    row=evaluate(n,count,1101,3)
    assert all(v<1e-9 for v in row["errors"].values())
    assert all(len(v["raw_ms"])==3 for v in row["variants"].values())

@pytest.mark.parametrize("reuse",[False,True])
def test_near_normalized_and_native_fault(reuse,monkeypatch):
    data,labels=workload(4,8,2202)
    data*=np.sqrt(1+4e-10)
    r=q.Result(data)
    np.testing.assert_allclose(_query(r,labels,reuse=reuse),
        [independent(data,label) for label in labels],atol=1e-9,rtol=0)
    monkeypatch.setattr(Statevector,"expectation_value",lambda *a,**k:complex(0,float("nan")))
    with pytest.raises(ArithmeticError):
        _query(r,labels,reuse=reuse)

@pytest.mark.parametrize("reuse",[False,True])
def test_research_preflight(reuse,monkeypatch):
    r=q.bell().run()
    monkeypatch.setattr(Statevector,"expectation_value",lambda *a,**k:pytest.fail("invalid request executed"))
    for labels in ((),("XX","BAD"),("XX","XX"),("xx",)):
        with pytest.raises(ValueError):
            _query(r,labels,reuse=reuse)
