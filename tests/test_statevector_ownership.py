import pytest
from research.statevector_ownership import evaluate

@pytest.mark.parametrize("kind",["identity","local","far","phase","mixed"])
def test_native_output_ownership(kind):
    row=evaluate(4,kind,reps=2)
    assert row["max_error"]<1e-9
    assert row["ownership"]["chain"]
    if row["ownership"]["aliases_input"]:assert row["adopted"]==0

@pytest.mark.parametrize("kind",["identity","mixed"])
def test_large_output_ownership(kind):
    row=evaluate(12,kind,reps=2)
    assert row["max_error"]<1e-9
