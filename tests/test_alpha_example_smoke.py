"""Keep the authored learning path executable in required test CI."""
from pathlib import Path
import runpy

def test_alpha_mathematical_workflow_example(capsys):
    example=Path(__file__).resolve().parents[1]/"examples"/"alpha_mathematical_workflow.py"
    runpy.run_path(str(example),run_name="__main__")
    assert "Phase defect detected and witness reproduced." in capsys.readouterr().out
