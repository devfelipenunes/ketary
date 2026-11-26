import json
import pytest
import ketary as q
from agent_workflow import investigate

def test_evidence_driven_repair():
    # Deliberately altered final gate, with equal probabilities but different state.
    reference=q.bell().x(0)
    mutant=q.bell().z(0)
    report=investigate(reference,mutant,bits=["00","11"])
    assert report["checks"]["operator"]["status"]=="FAIL"
    assert report["diagnosis"]["step_index"]==3
    assert report["diagnosis"]["actual_operation"]=="z"
    assert report["diagnosis"]["reference_operation"]=="x"
    # Trusted repair fixture. Verification is stronger than comparing output alone.
    repaired=q.bell().x(0)
    assert investigate(reference,repaired,bits=["01","10"])["checks"]["operator"]["status"]=="PASS"
    assert json.loads(json.dumps(report,allow_nan=False))==report

def test_relative_phase_evidence_not_probability_only():
    reference=q.bell().z(0).z(0)
    mutant=q.bell().z(0).rz(0,0)
    report=investigate(reference,mutant,bits=["00","11"])
    assert report["checks"]["distribution"]["status"]=="PASS"
    assert report["checks"]["state"]["status"]=="FAIL"
    assert report["checks"]["operator"]["status"]=="FAIL"
    assert report["diagnosis"]["step_index"]==4
