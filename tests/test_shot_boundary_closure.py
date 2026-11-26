"""Native count retrieval and schema failures must never become statistics."""
import sys
import types
import math
import pytest
import ketary as q
import qiskit
from qiskit.exceptions import QiskitError


def fake_result(monkeypatch, result):
    class Backend:
        def __init__(self, **kw): pass
        def run(self, *a, **kw): return self
        def result(self): return result
    module = types.ModuleType("qiskit_aer")
    module.AerSimulator = Backend
    monkeypatch.setitem(sys.modules, "qiskit_aer", module)
    monkeypatch.setattr(qiskit, "transpile", lambda circuit, **kw: circuit)


def test_missing_native_counts(monkeypatch):
    error = QiskitError("No counts for experiment")
    def get_counts():
        raise error
    fake_result(monkeypatch, types.SimpleNamespace(success=True, get_counts=get_counts))
    c = q.Circuit.classical(1, 1).measure(0, 0)
    before = c.to_qiskit()
    with pytest.raises(RuntimeError, match="native shot counts unavailable") as info:
        c.run_shots(shots=8, seed=1)
    assert info.value.__cause__ is error
    assert c.to_qiskit() == before


def test_failed_native_result_never_reads_counts(monkeypatch):
    fake_result(monkeypatch, types.SimpleNamespace(
        success=False, get_counts=lambda: pytest.fail("failed backend queried")))
    with pytest.raises(RuntimeError, match="native shot execution failed"):
        q.Circuit.classical(1, 1).measure(0, 0).run_shots(shots=8)


@pytest.mark.parametrize("counts", [None, [], {"":8}, {"00":8}, {"x":8},
    {"0":True}, {"0":8.0}, {"0":-1,"1":9}, {"0":0,"1":8}, {"0":7}])
def test_single_register_schema_precedes_arithmetic(monkeypatch, counts):
    fake_result(monkeypatch, types.SimpleNamespace(success=True, get_counts=lambda: counts))
    with pytest.raises(RuntimeError, match="unexpected native count schema"):
        q.Circuit.classical(1, 1).measure(0, 0).run_shots(shots=8)


@pytest.mark.parametrize("shots,zeros", [(10,5),(10000,5000),(10000,10000),(10000,0)])
def test_statistical_independent_interval(shots, zeros):
    contract=q.StatisticalContract(1, probabilities={"0":.5,"1":.5}, margin=.1, confidence=.95)
    result=q.ShotResult(shots,1,1,(("0",zeros),("1",shots-zeros)),((1,0,0),))
    report=contract.verify(result)
    radius=math.sqrt(math.log(4/.05)/(2*shots))
    for label, estimate in [("0",zeros/shots),("1",1-zeros/shots)]:
        lo,hi=max(0,estimate-radius),min(1,estimate+radius)
        assert report["checks"][label]["interval"] == pytest.approx([lo,hi])
        expected="FAIL" if hi<.4 or lo>.6 else "PASS" if lo>=.4 and hi<=.6 else "INCONCLUSIVE"
        assert report["checks"][label]["status"]==expected
