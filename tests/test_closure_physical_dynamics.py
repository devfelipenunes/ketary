import numpy as np
import pytest
import ketary as q
from research.closure_physical_dynamics import CASES,evaluate

@pytest.mark.parametrize("name",CASES)
def test_matched_physical_dynamics(name):
    row=evaluate(name,reps=2)
    assert set(row["paths"])=={"sdk","native"}
    assert all(len(p["run"]["raw_ms"])==2 for p in row["paths"].values())

def test_noncommuting_requires_explicit_exact_or_product():
    c=q.Circuit(3).h(0);before=c.to_qiskit()
    with pytest.raises(q.UnsupportedOperation):
        c.evolve(q.X(0)+q.Z(0),time=.3)
    assert c.to_qiskit()==before
    with pytest.raises(ValueError):
        c.evolve_exact(q.X(0),time=np.nan)
    assert c.to_qiskit()==before
