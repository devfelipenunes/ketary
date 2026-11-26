import numpy as np
import pytest
from research.qml_workflow_qualification import evaluate,analytic_angle_train,TRAIN,HELD,PAIRS

@pytest.mark.parametrize("name",["angle","parity","kernel","regression"])
def test_matched_qml_workload(name):
    row=evaluate(name,3)
    assert row["max_error"]<=1e-9
    assert row["sdk_gates"]==row["native_gates"]

def test_fixed_splits_and_objective_history():
    assert not set(TRAIN)&set(HELD)
    hist,held,t=analytic_angle_train()
    assert hist.shape==(8,3) and len(held)==4
    assert hist[-1,0]<hist[0,0]
    assert len(PAIRS)==4
