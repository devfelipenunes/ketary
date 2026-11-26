import pytest
import ketary as q
from research.closure_arithmetic_compare import evaluate
from research.abstraction_advanced import add_register

@pytest.mark.parametrize("n",[1,2,3])
def test_matched_modular_adder(n):
    row=evaluate(n,reps=2)
    assert set(row["paths"])=={"sdk","native"}
    assert all(len(p["run"]["raw_ms"])==2 for p in row["paths"].values())

def test_adder_bounds():
    with pytest.raises(q.ResourceLimit):add_register(5)
    with pytest.raises(ValueError):add_register(0)
