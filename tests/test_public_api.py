"""Public facade and module-boundary regressions."""
import subprocess
import sys
import ketary as q

def test_public_exports():
    assert set(q.__all__) == {
        "Circuit", "Result", "CheckResult", "TraceStep", "TraceComparison", "ResourceReport",
        "ResourceLimit", "UnsupportedOperation", "from_qiskit", "bell", "ghz", "constant_oracle", "parity_oracle", "deutsch_jozsa",
    }
    assert type(q.bell()) is q.Circuit
    assert type(q.ghz(3)) is q.Circuit
    assert isinstance(q.bell().run(), q.Result)
    assert isinstance(q.bell().debug.trace()[0], q.TraceStep)

def test_import_does_not_load_qiskit():
    subprocess.run([sys.executable, "-c",
                    "import sys, ketary; assert 'qiskit' not in sys.modules"],
                   check=True)

def test_facade_keeps_exception_identity():
    import pytest
    with pytest.raises(q.ResourceLimit):
        q.bell().run(max_bytes=1)
    with pytest.raises(q.UnsupportedOperation):
        q.bell().run(mode="hardware")
