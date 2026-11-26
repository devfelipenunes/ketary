"""State-check admission must precede conversion of caller-owned targets."""
import numpy as np
import pytest
import ketary as q


class Unconvertible:
    def __array__(self, *args, **kwargs):
        pytest.fail("target converted before control validation")


@pytest.mark.parametrize("kwargs", [
    {"atol": -1}, {"atol": float("nan")}, {"atol": float("inf")},
    {"ignore_global_phase": 1}, {"ignore_global_phase": None},
])
def test_invalid_controls_do_not_convert_target(kwargs):
    result = q.Result([1, 0])
    with pytest.raises(ValueError):
        result.test.state(Unconvertible(), **kwargs)


@pytest.mark.parametrize("as_snapshot", [False, True])
@pytest.mark.parametrize("ignore", [False, True])
def test_valid_controls_keep_phase_semantics(as_snapshot, ignore):
    result = q.Result([1, 0])
    raw = np.array([1j, 0j])
    target = q.Result(raw) if as_snapshot else raw
    report = result.test.state(target, ignore_global_phase=ignore, atol=1e-9)
    assert report.status == ("PASS" if ignore else "FAIL")
    assert report.actual == pytest.approx(0 if ignore else np.sqrt(2))
    assert np.array_equal(result.math.statevector(), [1, 0])
    assert np.array_equal(raw, [1j, 0j])
