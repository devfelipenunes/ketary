"""Reproducible execution study on hash-pinned public QASMBench files.

Only QASM data is fetched; upstream Python is not imported or executed.
Terminal measurements and barriers are excluded from the explicit unitary
projection. Dynamic programs are reported as outside this scope.
Run with --fetch-public or --root /path/to/pinned/checkout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen
import numpy as np
import qiskit
from qiskit import QuantumCircuit, qasm2, transpile
from qiskit.quantum_info import Operator, Statevector
import ketary as q

MANIFEST=Path(__file__).with_name("published_circuit_manifest.json")
MAX_SOURCE=64*1024
TOL=1e-9

def source_bytes(entry,commit,root):
    if root is not None:
        with (root/entry["path"]).open("rb") as stream:
            data=stream.read(MAX_SOURCE+1)
    else:
        url=f"https://raw.githubusercontent.com/pnnl/QASMBench/{commit}/{entry['path']}"
        with urlopen(url,timeout=20) as stream:
            data=stream.read(MAX_SOURCE+1)
    if len(data)>MAX_SOURCE:
        raise ValueError("source exceeds limit")
    actual=hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
    if actual!=entry["git_blob_sha1"]:
        raise ValueError("source blob hash mismatch")
    return data

def project_unitary(circuit):
    """Copy original gate order and phase; reject all nonterminal readout."""
    if circuit.num_qubits>10 or len(circuit.data)>4096 or circuit.parameters:
        return None,"width, instruction or parameter scope"
    logical=QuantumCircuit(circuit.num_qubits,global_phase=circuit.global_phase)
    readout=False
    removed={"measure":0,"barrier":0}
    for item in circuit.data:
        op=item.operation
        if op.name=="barrier":
            removed["barrier"]+=1
            continue
        if op.name=="measure":
            readout=True
            removed["measure"]+=1
            continue
        if readout:
            return None,"operation after measurement"
        if item.clbits or op.name in ("reset","initialize","if_else","while_loop","for_loop","switch_case"):
            return None,"nonunitary or classical operation"
        logical.append(op,[circuit.find_bit(w).index for w in item.qubits])
    return logical,removed

def analyze(source):
    # qelib1 is the only allowed include, resolved by the native parser.
    clean=re.sub(r"//[^\n]*","",source)
    if any(name!="qelib1.inc" for name in re.findall(r'\binclude\s+"([^"]+)"',clean)):
        raise ValueError("unexpected include")
    try:
        native=qasm2.loads(source,include_path=(),custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    except qasm2.QASM2Error as exc:
        return {"status":"PARSER_UNSUPPORTED","reason":str(exc)[:300]}
    logical,removed=project_unitary(native)
    row={"qubits":native.num_qubits,"native_instructions":len(native.data)}
    if logical is None:
        return {**row,"status":"OUTSIDE_UNITARY_SCOPE","reason":removed}
    row.update({"removed":removed,"projected_gates":len(logical.data)})
    try:
        candidate=q.from_qiskit(logical)
        path="direct"
    except (ValueError,TypeError) as exc:
        row["direct_rejection"]=str(exc)[:200]
        # The translation is a separate, explicitly identified native step.
        normalized=transpile(logical,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=7)
        candidate=q.from_qiskit(normalized)
        path="native_basis_translation"
    row.update({"import_path":path,"ketary_gates":len(candidate.to_qiskit().data)})
    n=logical.num_qubits
    errors=[]
    # Independent complex input in addition to basis and superposition states.
    rng=np.random.default_rng(501+n)
    vector=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    vector/=np.linalg.norm(vector)
    for state in ("0"*n,"1"*n,"+"*n,vector):
        sv=Statevector.from_label(state) if isinstance(state,str) else Statevector(state)
        expected=sv.evolve(logical).data
        # Use native vector for plus labels; Ketary.run string is basis-only.
        actual=candidate.run(initial_state=sv.data).math.statevector()
        errors.append(float(np.max(np.abs(expected-actual))))
    row["max_state_error"]=max(errors)
    row["tested_inputs"]=4
    if n<=6:
        err=float(np.max(np.abs(Operator(logical).data-Operator(candidate.to_qiskit()).data)))
        row["max_operator_error"]=err
        row["status"]="MATCHED_OPERATOR_AND_STATES" if max(err,*errors)<=TOL else "MISMATCH"
    else:
        row["status"]="MATCHED_SELECTED_STATES" if max(errors)<=TOL else "MISMATCH"
    return row

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--root",type=Path)
    group.add_argument("--fetch-public",action="store_true")
    args=parser.parse_args()
    manifest=json.loads(MANIFEST.read_text())
    rows=[]
    for entry in manifest["files"]:
        row={"name":entry["name"],"git_blob_sha1":entry["git_blob_sha1"]}
        try:
            row.update(analyze(source_bytes(entry,manifest["commit"],args.root).decode("utf-8")))
        except Exception as exc:
            row.update(status="ERROR",reason=f"{type(exc).__name__}: {str(exc)[:300]}")
        rows.append(row)
    summary={"source":manifest["repository"],"commit":manifest["commit"],
             "qiskit":qiskit.__version__,"tolerance":TOL,"cases":rows}
    for label in ("MATCHED_OPERATOR_AND_STATES","MATCHED_SELECTED_STATES","PARSER_UNSUPPORTED",
                  "OUTSIDE_UNITARY_SCOPE","MISMATCH","ERROR"):
        summary[label.lower()]=sum(row["status"]==label for row in rows)
    print(json.dumps(summary,indent=2,allow_nan=False))
    # A diagnostic must not count exclusions or parse errors as matches.
    return int(summary["mismatch"]>0 or summary["error"]>0 or
               summary["matched_operator_and_states"]+summary["matched_selected_states"]<10)

if __name__=="__main__":
    raise SystemExit(main())
