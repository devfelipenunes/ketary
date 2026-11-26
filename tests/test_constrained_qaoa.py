"""Paired constrained optimization workflows and objective negative controls."""
import pytest
from research.constrained_qaoa import evaluate,objective,feasible,KINDS

@pytest.mark.parametrize("kind",KINDS)
def test_constrained_qaoa_paired_grid(kind):
    result=evaluate(kind)
    assert len(result["rows"])==25
    assert max(r["max_state_residual"] for r in result["rows"])<1e-9
    assert all(-1e-12<=r["feasible_probability"]<=1+1e-12 for r in result["rows"])
    assert result["grid_best"]["energy"]>=result["exact_classical_minimum"]-1e-9
    for label in result["optimum_labels"]:
        assert feasible(kind,tuple(int(x) for x in reversed(label)))

def test_objective_negative_controls():
    assert objective("independent_set",(0,1,0,1))==-4
    assert not feasible("independent_set",(1,1,0,0))
    assert objective("vertex_cover",(1,0,1,0))==2
    assert not feasible("vertex_cover",(0,0,0,0))
    assert not feasible("portfolio",(1,1,1,1))
    assert objective("portfolio",(1,1,1,1))>objective("portfolio",(1,0,0,1))
    with pytest.raises(ValueError):evaluate("unsupported")
