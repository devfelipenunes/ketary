"""Isolated public-contract oracles for replay, verification and resource faults."""
import json,math
import numpy as np
import pytest
import ketary as q

def payload():
    return json.loads(q.Circuit(1).to_json())

def decode(data):
    return q.Circuit.from_json(json.dumps(data,separators=(",",":")))

def test_replay_duplicate_key():
    s=q.Circuit(1).to_json()
    s=s.replace('"num_qubits":1','"num_qubits":1,"num_qubits":1')
    with pytest.raises(ValueError,match="duplicate"):q.Circuit.from_json(s)

def test_replay_unknown_field():
    data=payload();data["extra"]="ignored?"
    with pytest.raises(ValueError,match="fields"):decode(data)

def test_replay_unknown_schema():
    data=payload();data["schema_version"]=2
    with pytest.raises(ValueError,match="schema"):decode(data)

def test_replay_boolean_schema():
    data=payload();data["schema_version"]=True
    with pytest.raises(ValueError,match="schema"):decode(data)

def test_replay_producer_cap():
    data=payload();data["producer"]["python"]="x"*101
    with pytest.raises(ValueError,match="producer"):decode(data)

def test_replay_width_cap():
    data=payload();data["num_qubits"]=23
    with pytest.raises(q.ResourceLimit):decode(data)

def test_replay_gate_cap():
    data=payload();data["operations"]=[{"gate":"h","wires":[0],"params":[]}]*10001
    with pytest.raises(q.ResourceLimit):decode(data)

def test_replay_byte_cap():
    s=q.Circuit(1).to_json()
    s+=" "*(1024*1024+1-len(s))
    with pytest.raises(q.ResourceLimit):q.Circuit.from_json(s)

def test_replay_strict_phase():
    c=q.Circuit(1).h(0).evolve(q.I(),time=.81)
    np.testing.assert_allclose(q.Circuit.from_json(c.to_json()).run().math.statevector(),np.exp(-.81j)*np.ones(2)/np.sqrt(2),atol=1e-9)

def test_replay_control_target_order():
    c=q.Circuit(2).cx(0,1)
    r=q.Circuit.from_json(c.to_json()).run(initial_state="01")
    assert r.math.probability("11")==pytest.approx(1.)

def test_replay_negative_rotation():
    c=q.Circuit(1).ry(-.71,0)
    r=q.Circuit.from_json(c.to_json()).run()
    np.testing.assert_allclose(r.math.statevector(),[np.cos(.71/2),-np.sin(.71/2)],atol=1e-9)

def test_bool_integer_rejected():
    with pytest.raises(ValueError):q.Circuit(2).x(True)

def test_bool_real_rejected():
    with pytest.raises(ValueError):q.Observable({"X":True})

def test_bool_angle_rejected():
    with pytest.raises(ValueError):q.Circuit(1).ry(True,0)

def test_payload_preflight():
    with pytest.raises(q.ResourceLimit):q.Circuit(1).run(max_bytes=31)

def test_pauli_mapping_order():
    r=q.basis("01").run()
    assert r.math.expectation({0:"Z"})==pytest.approx(-1.)

def test_operator_width_fail():
    assert q.Circuit(1).test.equivalent(q.Circuit(2)).status=="FAIL"

def test_operator_budget_unsupported():
    c=q.bell()
    assert c.test.equivalent(c,max_bytes=1).status=="UNSUPPORTED"

def test_operator_default_strict_phase():
    c=q.Circuit(1).evolve(q.I(),time=.37)
    assert c.test.equivalent(q.Circuit(1)).status=="FAIL"
    assert c.test.equivalent(q.Circuit(1),ignore_global_phase=True).status=="PASS"

def test_conditional_mass_normalization():
    r=q.bell().run()
    assert r.math.conditional_probability({1:0},{0:0})==pytest.approx(1.)

def test_conditional_conflicting_events():
    r=q.bell().run()
    assert r.math.conditional_probability({0:1},{0:0})==0.

def test_pure_trace_distance():
    r=q.Circuit(1).run()
    assert r.math.trace_distance([1/np.sqrt(2),1/np.sqrt(2)])==pytest.approx(1/np.sqrt(2))

def test_top_probability_ties():
    r=q.Circuit(2).h([0,1]).run()
    assert list(r.math.top_probabilities(k=2))==["00","01"]

def test_pauli_variance_square():
    r=q.Circuit(1).ry(.71,0).run()
    assert r.math.variance("Z")==pytest.approx(np.sin(.71)**2)

def test_entropy_base_two():
    assert q.bell().run().math.entropy(([0],[1]))==pytest.approx(1.)

def shot(shots,counts,measured=True):
    return q.ShotResult(shots,1,0,tuple(counts.items()),((1,0,0),) if measured else ())

def test_statistical_unmeasured_unsupported():
    c=q.StatisticalContract(1,probabilities={"0":.5})
    assert c.verify(shot(8,{"0":4,"1":4},False)).status=="UNSUPPORTED"

def test_statistical_union_bound():
    c=q.StatisticalContract(1,probabilities={"0":.5,"1":.5},confidence=.95)
    report=c.verify(shot(100,{"0":50,"1":50}))
    radius=math.sqrt(math.log(4/.05)/200)
    np.testing.assert_allclose(report["checks"]["0"]["interval"],[.5-radius,.5+radius],atol=1e-12,rtol=0)

def test_statistical_overlap_inconclusive():
    c=q.StatisticalContract(1,probabilities={"0":.5},margin=.1)
    assert c.verify(shot(8,{"0":4,"1":4})).status=="INCONCLUSIVE"

def test_statistical_bad_total_rejected():
    c=q.StatisticalContract(1,probabilities={"0":.5})
    with pytest.raises(ValueError,match="shot counts"):c.verify(shot(10,{"0":4,"1":4}))

def test_contract_failure_precedence():
    report=q.bell().run().verify(normalized=True,probabilities={"00":1.})
    assert report.status=="FAIL"

def test_optimize_different_wires():
    c=q.Circuit(2).x(0).x(1)
    assert c.optimize().run().math.probability("11")==pytest.approx(1.)

def test_optimize_rotation_phase_strict():
    c=q.Circuit(1).rx(0.,0).rx(2*np.pi,0)
    np.testing.assert_allclose(c.optimize().run().math.statevector(),[-1,0],atol=1e-9,rtol=0)

def test_result_rejects_unnormalized():
    with pytest.raises(ValueError):q.Result([2.,0.])

def test_result_caller_ownership():
    v=np.array([1.,0.],complex);r=q.Result(v)
    assert v.flags.writeable
    v[:]=[0,1]
    assert r.math.probability("0")==pytest.approx(1.)
