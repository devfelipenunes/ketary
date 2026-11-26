"""Combined integration of the five-front candidate, not separate branch counts."""
import numpy as np
import pytest
import ketary as q
from scipy.linalg import expm
from qiskit.quantum_info import Statevector
from research.observable_reuse import embed
from research.architecture_inventory import inspect

def test_combined_local_evolution_query_and_contract(monkeypatch):
    assert not inspect()["eager_cycles"]
    t=q.Circuit.parameter("t")
    local=q.Observable({"XY":.7,"YX":-.4,"II":.2})
    H=embed(local,[2,0],width=3)
    template=q.Circuit.symbolic(3).h(range(3)).evolve(H,time=t)
    x=np.array([[0,1],[1,0]]);y=np.array([[0,-1j],[1j,0]]);I=np.eye(2)
    dense=.7*np.kron(np.kron(y,I),x)-.4*np.kron(np.kron(x,I),y)+.2*np.eye(8)
    value=.31;v=expm(-1j*value*dense)@(np.ones(8)/np.sqrt(8))
    bound=template.bind([value])
    plan=bound.plan(bits=["000","111"],paulis=["YIX","XIY"])
    report=plan.run()
    assert report["evidence"]["basis"]["000"]["probability"]==pytest.approx(abs(v[0])**2)
    result=bound.run()
    np.testing.assert_allclose(result.math.statevector(),v,atol=1e-9,rtol=0)
    target=float(np.vdot(v,dense@v).real)
    assert bound.contract(expectations={H:target}).verify(result).status=="PASS"
    bound.x(0)
    assert plan.run()==report
    assert template.parameters==(t,)
    monkeypatch.setattr(Statevector,"expectation_value",lambda *a,**k:complex(.5,float("nan")))
    with pytest.raises(ArithmeticError):plan.run()
    with pytest.raises(ArithmeticError):result.math.expectation(H)
