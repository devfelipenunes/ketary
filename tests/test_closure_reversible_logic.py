import pytest
import ketary as q
from research.closure_reversible_logic import evaluate
from research.abstraction_advanced import truth_oracle

@pytest.mark.parametrize("kind",["increment","comparison","composition"])
@pytest.mark.parametrize("n",[2,3])
def test_reversible_logic(kind,n):
    row=evaluate(kind,n,reps=2)
    assert set(row["paths"])=={"sdk","native"}
    assert all(len(p["run"]["raw_ms"])==2 for p in row["paths"].values())

def test_truth_oracle_bounds():
    with pytest.raises(q.ResourceLimit):truth_oracle(4,[])
    with pytest.raises(ValueError):truth_oracle(2,["00","00"])
    with pytest.raises(ValueError):truth_oracle(2,["01","bad"])
