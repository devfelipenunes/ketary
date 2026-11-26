import pytest
from research.workflow_depth import evaluate,gradient_counterexample
@pytest.mark.parametrize("kind",["qaoa","vqe"])
@pytest.mark.parametrize("n",[3,4,5])
def test_objective_workflow(kind,n):
    row=evaluate(kind,n,reps=3)
    assert all(v["max_error"]<1e-9 for v in row["variants"].values())

@pytest.mark.parametrize("t",[.17,.37,-.81])
def test_shared_parameter_shift_counterexample(t):
    g=gradient_counterexample(t)
    assert abs(g["naive"]-g["analytic"])>.1
    assert abs(g["occurrence_sum"]-g["analytic"])<1e-9
    assert abs(g["finite_difference"]-g["analytic"])<1e-8
