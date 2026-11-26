from pathlib import Path
import runpy

def test_complete_workflows():
    path=Path(__file__).resolve().parents[1]/"research"/"complete_workflows.py"
    assert runpy.run_path(str(path))["run"]()["passed"]==6
