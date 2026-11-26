import pytest
from research.qiskit_workflow_coverage import CASES,evaluate

@pytest.mark.parametrize("case",CASES,ids=[x[0] for x in CASES])
def test_qiskit_workflow_coverage(case):
    row=evaluate(case)
    if case[3]=="gap":
        assert row["status"]=="rejected", "capability changed; review and update classification"
    else:
        assert row["status"]=="matched" and row["max_error"]<1e-9
