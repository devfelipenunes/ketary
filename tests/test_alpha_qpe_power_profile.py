import pytest
import ketary as q
from research.alpha_qpe_power_profile import run

def test_qpe_power_profile():
    assert len(run(1101,1))==9

@pytest.mark.parametrize("phase",[-.01,1.,float("nan")])
def test_qpe_invalid_phase(phase):
    with pytest.raises(ValueError):
        q.phase_estimation(phase)

def test_qpe_precision_cap():
    with pytest.raises(q.ResourceLimit):
        q.phase_estimation(.25,precision=13)
