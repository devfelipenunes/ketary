"""Cross-workflow contracts and fail-before-allocation replay/plan checks."""
import json
import itertools
import numpy as np
import pytest
import ketary as q

@pytest.mark.parametrize("angle",[-.7,.21,1.3])
def test_reusable_contract_across_distinct_programs(angle,monkeypatch):
    # Two different implementations of the same entangled snapshot.
    expected=np.array([np.cos(angle/2),0,0,np.sin(angle/2)],complex)
    a=q.Circuit(2).ry(angle,0).cx(0,1)
    b=q.Circuit.prepare_state(expected)
    good=[a.run(),b.run()]
    wrong=a.copy().z(0).run()
    p={"00":float(abs(expected[0])**2),"11":float(abs(expected[3])**2)}
    h=q.X(0)@q.X(1)
    e={h:float(np.sin(angle)),"ZZ":1.}
    contract=q.Contract(2,probabilities=p,expectations=e,normalized=True)
    saved=contract.to_dict()
    p["00"]=0.;e[h]=99.
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("contract reran circuit"))
    for result in good:
        report=contract.verify(result);report.require()
        assert report.status=="PASS" and "not operator equivalence" in report.scope
        assert json.loads(report.to_json())==report.to_dict()
    assert contract.verify(wrong).status=="FAIL"
    with pytest.raises(AssertionError):contract.verify(wrong).require()
    with pytest.raises(ValueError):contract.verify(q.Result([1,0]))
    with pytest.raises(TypeError):contract.verify(object())
    assert contract.to_dict()==saved

@pytest.mark.parametrize("state",[[1,0],[0,1]])
def test_contract_independent_basis_and_variational_workloads(state):
    v=np.asarray(state,complex)
    basis=q.Circuit.prepare_state(v)
    t=q.Circuit.parameter("t")
    variational=q.Circuit.symbolic(1).ry(t,0).bind({t:0. if state[0] else np.pi})
    target=float(abs(v[0])**2-abs(v[1])**2)
    contract=q.Contract(1,expectations={"Z":target},normalized=True)
    for c in (basis,variational):contract.verify(c.run()).require()

@pytest.mark.parametrize("query",[
    {"bits":["00","00"]},{"paulis":["XX","XX"]},{"subsystems":[(),(1,)]},
    {"subsystems":[(0,0)]},{"subsystems":[(2,)]},{"subsystems":[(0,),(0,)]},
    {"bits":["00"],"subsystems":itertools.repeat((0,))},
])
def test_invalid_query_plan_before_replay(query,monkeypatch):
    c=q.bell()
    monkeypatch.setattr(q.Circuit,"to_json",lambda *a,**k:pytest.fail("replay preceded query validation"))
    with pytest.raises(ValueError):c.plan(**query)

def test_aggregate_plan_budget_and_report_defense(monkeypatch):
    c=q.Circuit(3).h(0).cx(0,2)
    plan=c.plan(bits=["000","101"],subsystems=[(2,0),(0,2),(1,)])
    expected=plan.estimate()
    assert expected["density_output_bytes"]==16*(16+16+4)
    exact=expected["state_payload_bytes"]+expected["density_output_bytes"]
    c.x(1)
    calls=[];run=q.Circuit.run
    def counted(self,*a,**kw):calls.append(1);return run(self,*a,**kw)
    monkeypatch.setattr(q.Circuit,"run",counted)
    with pytest.raises(q.ResourceLimit):plan.run(max_bytes=exact-1)
    assert not calls
    report=plan.run(max_bytes=exact)
    assert len(calls)==1
    expected_density=np.zeros((4,4));expected_density[np.ix_([0,3],[0,3])]=.5
    np.testing.assert_allclose(report["density_matrices"][0]["real"],expected_density,atol=1e-9,rtol=0)
    report["density_matrices"][0]["real"][0][0]=99.
    report["estimate"]["gate_count"]=99
    fresh=plan.run(max_bytes=exact)
    assert len(calls)==2 and plan.estimate()==expected
    np.testing.assert_allclose(fresh["density_matrices"][0]["real"],expected_density,atol=1e-9,rtol=0)

@pytest.mark.parametrize("kind",["late_gate","late_wires","late_params","producer","extra","surrogate","deep","bytes"])
def test_replay_rejects_entire_artifact_before_native_allocation(kind,monkeypatch):
    import ketary._replay as replay
    raw=json.loads(q.bell().to_json())
    if kind=="late_gate":raw["operations"].append({"gate":"unknown","wires":[0],"params":[]})
    elif kind=="late_wires":raw["operations"].append({"gate":"cx","wires":[1,1],"params":[]})
    elif kind=="late_params":raw["operations"].append({"gate":"rx","wires":[0],"params":[float("nan")]})
    elif kind=="producer":raw["producer"]["python"]=""
    elif kind=="extra":raw["extra"]=0
    payload=json.dumps(raw)
    if kind=="surrogate":payload="\ud800"
    elif kind=="deep":payload="["*2000+"]"*2000
    elif kind=="bytes":payload=" "*(1024*1024+1)
    monkeypatch.setattr(replay,"_sdk",lambda:pytest.fail("native allocation preceded full validation"))
    with pytest.raises(q.ResourceLimit if kind=="bytes" else ValueError):q.Circuit.from_json(payload)

@pytest.mark.parametrize("angle",[.31,.73,1.1])
def test_intermediate_defect_and_reproducible_terminal_witness(angle):
    ref=q.Circuit(2).ry(angle,0).checkpoint("prepare").cx(0,1).checkpoint("entangle").z(1).checkpoint("finish")
    bad=q.Circuit(2).ry(angle,0).checkpoint("prepare").cx(0,1).checkpoint("entangle").x(1).checkpoint("finish")
    before=bad.to_qiskit()
    diag=bad.debug.compare(ref,ignore_global_phase=False)
    assert diag.check.status=="FAIL" and diag.step_index==3
    assert (diag.actual_operation,diag.reference_operation)==("x","z")
    assert diag.to_dict()["step_index"]==3
    comparison=bad.test.compare(ref,inputs=["00"],ignore_global_phase=False)
    assert comparison["status"]=="FAIL"
    e=q.Evidence.from_dict(comparison["evidence"])
    assert q.Evidence.from_json(e.to_json()).reproduce()["reproduced"]
    assert bad.to_qiskit()==before
