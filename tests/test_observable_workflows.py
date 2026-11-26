import pytest
from research.observable_workflows import evaluate
@pytest.mark.parametrize("kind",["read","evolve"])
@pytest.mark.parametrize("n",[4,6,8])
def test_observable_workflow(kind,n):
    row=evaluate(kind,n,reps=3)
    assert set(row["variants"])=={"manual","embedding","qiskit"}
    assert all(v["max_error"]<1e-9 for v in row["variants"].values())
