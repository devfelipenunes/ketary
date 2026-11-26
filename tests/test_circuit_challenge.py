"""Execute every registered challenge; optional measured cases run in Aer CI."""
from collections import Counter
import pytest
from research.circuit_challenge import CASES,EXPECTED_COUNTS,run_case,manifest

def test_challenge_manifest():
    assert len(manifest())==100
    assert Counter(x["category"] for x in manifest())==EXPECTED_COUNTS
    assert len({x["id"] for x in manifest()})==100

@pytest.mark.parametrize("case",CASES,ids=[c.name for c in CASES])
def test_challenge(case):
    if case.category in ("dynamic","syndrome"):pytest.importorskip("qiskit_aer")
    assert run_case(case)<1e-9
