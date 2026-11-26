from pathlib import Path
import runpy

def test_first_verification():
    path=Path(__file__).resolve().parents[1]/"examples"/"first_verification.py"
    runpy.run_path(str(path),run_name="__main__")
