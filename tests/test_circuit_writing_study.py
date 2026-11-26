from pathlib import Path
import runpy

def test_matched_circuit_workloads():
    script=Path(__file__).resolve().parents[1]/"research/circuit_writing_study.py"
    report=runpy.run_path(str(script))["run"]()
    assert report["matched"]==report["total"]==8, report
