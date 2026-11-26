"""Locally authored fixtures; no network dependency in the regular test suite."""
import hashlib
from pathlib import Path
import runpy
import pytest
from qiskit import QuantumCircuit

STUDY=runpy.run_path(str(Path(__file__).resolve().parents[1]/"research/published_circuit_execution.py"))

def test_source_integrity(tmp_path):
    data=b"OPENQASM 2.0;\n"
    p=tmp_path/"x.qasm"
    p.write_bytes(data)
    entry={"path":"x.qasm","git_blob_sha1":hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()}
    assert STUDY["source_bytes"](entry,"ignored",tmp_path)==data
    p.write_bytes(data+b" ")
    with pytest.raises(ValueError,match="hash mismatch"):
        STUDY["source_bytes"](entry,"ignored",tmp_path)

def test_unitary_projection_scope():
    circuit=QuantumCircuit(2,2,global_phase=.2)
    circuit.h(0); circuit.cx(0,1); circuit.barrier()
    circuit.measure(0,0); circuit.measure(1,1)
    result,removed=STUDY["project_unitary"](circuit)
    assert len(result.data)==2 and removed=={"measure":2,"barrier":1}
    assert result.global_phase==circuit.global_phase
    circuit.x(1)
    assert STUDY["project_unitary"](circuit)==(None,"operation after measurement")

def test_native_original_and_basis_translation():
    bell='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;'
    result=STUDY["analyze"](bell)
    assert result["status"]=="MATCHED_OPERATOR_AND_STATES" and result["import_path"]=="direct"
    custom='OPENQASM 2.0; include "qelib1.inc"; gate foo a { h a; t a; } qreg q[1]; foo q[0];'
    result=STUDY["analyze"](custom)
    assert result["status"]=="MATCHED_OPERATOR_AND_STATES" and result["import_path"]=="native_basis_translation"
