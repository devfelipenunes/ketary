import pytest
from research.variational_applications import evaluate

@pytest.mark.parametrize("kind",["maxcut","spin_vqe"])
@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_complete_variational_workflow(kind,seed):
    row=evaluate(kind,seed)
    assert row["max_error"]<1e-9
    sign=-1 if kind=="maxcut" else 1
    for v in row["variants"].values():
        assert sign*v["final"]<=sign*v["initial"]+1e-8
        assert sign*v["final"]>=sign*row["reference_optimum"]-1e-8
