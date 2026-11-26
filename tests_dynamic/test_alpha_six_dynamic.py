import pytest
from research.alpha_six_dynamic import evaluate

@pytest.mark.parametrize("kind",["direct","nested"])
@pytest.mark.parametrize("random_input",[False,True])
def test_dynamic_closure_profile(kind,random_input):
    row=evaluate(kind,random_input,1101,reps=1,shots=2048)
    assert all(sum(p["counts"][0]["counts"].values())==2048 for p in row["paths"].values())
