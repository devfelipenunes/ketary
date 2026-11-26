import json
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from qiskit import QuantumCircuit
from collections import Counter

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_native_fields_preserve_logical_reports_and_replay(seed):
    rng=np.random.default_rng(seed)
    raw=QuantumCircuit(5,global_phase=.37)
    for _ in range(8):
        raw.ry(float(rng.normal()),4);raw.cx(4,0);raw.ccx(0,2,1);raw.swap(1,3)
    c=q.from_qiskit(raw)
    expected=[dict(index=i+1,gate=item.operation.name,wires=[raw.find_bit(w).index for w in item.qubits],
                   params=[float(p) for p in item.operation.params]) for i,item in enumerate(raw.data)]
    for start,limit in ((0,1),(3,12),(30,256),(len(expected),1)):
        assert c.inspect(start=start,limit=limit)["operations"]==expected[start:start+limit]
    report=c.resources.summary()
    assert report.gate_count==len(expected)
    assert report.two_qubit_gates==16 and report.three_plus_qubit_gates==8
    assert dict(report.by_gate)==dict(Counter(row["gate"] for row in expected))
    payload=c.to_json()
    data=json.loads(payload)
    assert data["operations"]==[{k:v for k,v in row.items() if k!="index"} for row in expected]
    np.testing.assert_allclose(Operator(q.Circuit.from_json(payload).to_qiskit()).data,Operator(raw).data,atol=1e-9,rtol=0)
    assert c.to_qiskit()==raw

def test_native_fields_keep_symbolic_inspection_error():
    a=q.Circuit.parameter("a")
    c=q.Circuit.symbolic(2).ry(a,0)
    with pytest.raises((TypeError,ValueError)):c.inspect()
    assert c.resources.summary().gate_count==1
