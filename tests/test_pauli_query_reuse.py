"""Call-local native handle reuse with independent numerical and fault oracles."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Statevector,SparsePauliOp
from research.pauli_query_attribution import independent

@pytest.mark.parametrize("seed",range(12))
@pytest.mark.parametrize("n",[2,3,4])
def test_real_and_complex_pauli_reuse(seed,n,monkeypatch):
    rng=np.random.default_rng(seed+11800)
    data=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    data*=np.sqrt(1+4e-10)/np.linalg.norm(data)
    r=q.Result(data)
    labels=list(map("".join,itertools.product("IXYZ",repeat=n)))
    chosen=tuple(str(x) for x in rng.choice(labels,8,replace=False))
    values={label:independent(data,label) for label in chosen}
    a=q.Observable({chosen[0]:.7,chosen[1]:-.4,chosen[2]:.2})
    rows=[a,chosen[0],a,chosen[3],{i:axis for i,axis in enumerate(reversed(chosen[4])) if axis!="I"}]
    exact=.7*values[chosen[0]]-.4*values[chosen[1]]+.2*values[chosen[2]]
    expected=[exact,values[chosen[0]],exact,values[chosen[3]],values[chosen[4]]]
    calls=[]
    handles=[]
    original=Statevector.expectation_value
    def track(self,op,*args,**kwargs):
        handles.append(self);calls.append(op.to_label())
        return original(self,op,*args,**kwargs)
    monkeypatch.setattr(Statevector,"expectation_value",track)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("hidden run"))
    np.testing.assert_allclose(r.math.expectations(rows),expected,atol=1e-9,rtol=0)
    assert calls==sorted(set(chosen[:5]))
    assert len({id(handle) for handle in handles})==1
    first=handles[0];calls.clear();handles.clear()
    pairs=[(chosen[0],.3+.4j),(chosen[1],-.6j),(chosen[0],-.1+.2j)]
    got=r.math.expectation_complex(SparsePauliOp.from_list(pairs))
    want=sum(coeff*values[label] for label,coeff in pairs)
    assert got==pytest.approx(want,abs=1e-9,rel=0)
    assert calls==sorted(set(chosen[:2]))
    assert len({id(handle) for handle in handles})==1
    assert handles[0] is not first
    np.testing.assert_array_equal(r.math.statevector(),data)

@pytest.mark.parametrize("kind",["real","complex"])
def test_preflight_and_late_native_failure(kind,monkeypatch):
    r=q.bell().run()
    before=r.math.statevector()
    calls=[]
    original=Statevector.expectation_value
    def fault(self,op,*args,**kwargs):
        calls.append(op.to_label())
        if len(calls)==2:
            return complex(.5,float("nan"))
        return original(self,op,*args,**kwargs)
    monkeypatch.setattr(Statevector,"expectation_value",fault)
    if kind=="real":
        with pytest.raises(ValueError):r.math.expectations(["XX","bad"])
        with pytest.raises(q.ResourceLimit):r.math.expectations(["XX","ZZ"],max_work=7)
        call=lambda:r.math.expectations(["ZZ","XX"])
    else:
        with pytest.raises(ValueError):r.math.expectation_complex(SparsePauliOp.from_list([("XX",1),("ZZ",complex(float("nan"),0))]))
        with pytest.raises(q.ResourceLimit):r.math.expectation_complex(SparsePauliOp.from_list([("XX",1),("ZZ",1)]),max_work=7)
        call=lambda:r.math.expectation_complex(SparsePauliOp.from_list([("ZZ",1),("XX",1)]))
    assert calls==[]
    with pytest.raises(ArithmeticError,match="invalid Hermitian Pauli"):
        call()
    assert calls==["XX","ZZ"]
    np.testing.assert_array_equal(r.math.statevector(),before)
