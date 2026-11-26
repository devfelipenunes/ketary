import numpy as np
import pytest
import ketary as q

def shots(n,a,b):
    return q.ShotResult(n,1,42,(("0",a),("1",b)),((1,0,0),))

def test_statistical_three_way():
    contract=q.StatisticalContract(1,probabilities={"0":.5,"1":.5},margin=.1)
    assert contract.verify(shots(10000,5000,5000))["status"]=="PASS"
    assert contract.verify(shots(10000,10000,0))["status"]=="FAIL"
    assert contract.verify(shots(10,5,5))["status"]=="INCONCLUSIVE"
    assert contract.verify(q.ShotResult(10,1,1,(("0",10),)))["status"]=="UNSUPPORTED"
    with pytest.raises(ValueError):
        contract.verify(shots(10,5,6))
    with pytest.raises(ValueError):
        q.StatisticalContract(1,probabilities={"0":.8,"1":.8})

def test_query_plan_freezes_circuit_and_runs_once(monkeypatch):
    c=q.bell()
    plan=c.plan(bits=["00"],paulis=["XX"],subsystems=[[0]])
    c.z(0)
    orig=q.Circuit.run
    calls=[]
    def run(self,*args,**kwargs):
        calls.append(1)
        return orig(self,*args,**kwargs)
    monkeypatch.setattr(q.Circuit,"run",run)
    assert plan.estimate()["simulation_count"]==1 and calls==[]
    with pytest.raises(q.ResourceLimit):
        plan.run(max_bytes=1)
    assert calls==[]
    result=plan.run()
    assert len(calls)==1
    assert result["evidence"]["expectations"]["XX"]==pytest.approx(1)
    np.testing.assert_allclose(result["density_matrices"][0]["real"],np.eye(2)/2)
    with pytest.raises(ValueError):
        c.plan(bits=["bad"])
