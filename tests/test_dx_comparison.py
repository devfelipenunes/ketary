from pathlib import Path
import runpy

def test_authored_dx_comparison():
    script=Path(__file__).resolve().parents[1]/"research"/"dx_comparison.py"
    data=runpy.run_path(str(script))["run"]()
    assert data["equivalent"]==11
