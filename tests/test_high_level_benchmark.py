"""High-level benchmark smoke executes semantic preflight for every family."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from high_level_benchmark import run

def test_high_level_semantic_preflight():
    data=run(3,7,smoke=True)
    assert len(data["cases"])==7
    assert all(len(row["samples"]["native"]["raw_ms"])==3 for row in data["cases"])
