import pytest
from research.evolution_refinement import CASES,evaluate
@pytest.mark.parametrize("case",CASES,ids=[c[0] for c in CASES])
@pytest.mark.parametrize("time",[.37,-.29])
def test_public_evolution_rewrite(case,time):
    row=evaluate(case,reps=3,t=time)
    assert max(v["max_error"] for v in row["variants"].values())<1e-9
    assert row["variants"]["public"]["basis_gates"]<=row["variants"]["prototype"]["basis_gates"]
