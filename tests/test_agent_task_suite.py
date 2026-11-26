"""Reference task integrity; no external model or generated code execution."""
import sys
from pathlib import Path
import pytest
from qiskit import QuantumCircuit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from agent_task_suite import run,validate

def test_reference_solutions_and_negative_oracle():
    result=run()
    assert len(result["tasks"])==8
    assert all(row["matched"] for row in result["tasks"])
    a,b=QuantumCircuit(1),QuantumCircuit(1,global_phase=.2)
    with pytest.raises(AssertionError):
        validate(a,b,"operator")
