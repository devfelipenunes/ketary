"""Shared binding path: complete preflight, strict phase and ownership."""
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator, Statevector
from ketary._ergonomics import SweepPlan
from research.sweep_binding_cost import evaluate

@pytest.mark.parametrize("route",["named","ordered"])
def test_sweep_matches_native_and_freezes_all_rows(route):
    p,t=q.Circuit.parameter("p"),q.Circuit.parameter("t")
    c=q.Circuit.symbolic(3).ry(p,0).rz(p+t,1).cx(0,2).evolve(q.I(),time=t)
    raw=c.to_qiskit()
    rows=[(.1,.2),(-.3,.4),(.5,-.6)]
    plan=c.sweep(p=[r[0] for r in rows],t=[r[1] for r in rows]) if route=="named" else c.sweep_rows(rows)
    assert plan.bindings==tuple(dict(zip(("p","t"),row,strict=True)) for row in rows)
    c.h(1)
    for row,payload,result in zip(rows,plan._payloads,plan.run(),strict=True):
        native=raw.assign_parameters(dict(zip((p,t),row,strict=True)))
        np.testing.assert_allclose(Operator(payload.to_qiskit()).data,Operator(native).data,rtol=0,atol=1e-9)
        np.testing.assert_allclose(result.math.statevector(),Statevector.from_instruction(native).data,rtol=0,atol=1e-9)
    a=plan.bindings[0];a["p"]=9
    assert plan.bindings[0]["p"]==.1

@pytest.mark.parametrize("route",["named","ordered"])
def test_sweep_preflights_every_row_before_assignment(route,monkeypatch):
    p=q.Circuit.parameter("p");c=q.Circuit.symbolic(2).ry(p,0)
    monkeypatch.setattr(q.Circuit,"_bind_numeric",lambda *a:pytest.fail("assigned before full row preflight"))
    monkeypatch.setattr(q.Circuit,"_bind_sweep_rows",lambda *a:pytest.fail("assigned before full row preflight"))
    with pytest.raises(ValueError):
        if route=="named":c.sweep(p=[.2,float("nan")])
        else:c.sweep_rows([[.2],[float("nan")]])

def test_sweep_keeps_bound_value_validation(monkeypatch):
    from ketary import _adapter
    p=q.Circuit.parameter("p");c=q.Circuit.symbolic(2).ry(p,0)
    seen=[];original=_adapter._validate_bound_values
    def check(raw):
        seen.append(raw);original(raw)
    monkeypatch.setattr(_adapter,"_validate_bound_values",check)
    c.sweep_rows([[.2],[.4]])
    assert len(seen)==2 and seen[0] is not seen[1]
    assert not seen[0].parameters and not seen[1].parameters

def test_sweep_keeps_subclass_public_dispatch():
    class Tracked(q.Circuit):
        def bind(self,*args,**kwargs):
            self.calls+=1
            return super().bind(*args,**kwargs)
    p=q.Circuit.parameter("p");c=Tracked(2);c._symbolic=True;c.calls=0;c.ry(p,0)
    c.sweep_rows([[.2],[.4]])
    assert c.calls==2

@pytest.mark.parametrize("n,layers,count",[(2,1,1),(4,4,8),(8,4,32)])
def test_sweep_cost_routes(n,layers,count):
    row=evaluate(n,layers,count,reps=2)
    assert all(len(v["raw_ms"])==2 for v in row["stages"].values())

@pytest.mark.parametrize("route",["named","ordered"])
def test_sweep_rejects_source_changed_by_input_iterator(route,monkeypatch):
    p,r=q.Circuit.parameter("p"),q.Circuit.parameter("r")
    c=q.Circuit.symbolic(2).ry(p,0)
    def values():
        c.ry(r,1)
        yield .2 if route=="named" else [.2]
    monkeypatch.setattr(q.Circuit,"_bind_numeric",lambda *a:pytest.fail("assigned stale parameter identities"))
    monkeypatch.setattr(q.Circuit,"_bind_sweep_rows",lambda *a:pytest.fail("assigned stale parameter identities"))
    with pytest.raises(ValueError,match="bindings must cover"):
        if route=="named":c.sweep(p=values())
        else:c.sweep_rows(values())
