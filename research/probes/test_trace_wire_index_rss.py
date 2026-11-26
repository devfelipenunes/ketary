import numpy as np
import pytest
import ketary as q
from ketary import _trace
from qiskit import QuantumCircuit,QuantumRegister
from research.trace_wire_index_rss import IndexedCursor,OriginalCursor,evaluate

@pytest.mark.parametrize("n",[4,8])
def test_indexed_trace_oracle(n):
    row=evaluate(n,32,3)
    assert max(row["errors"].values())<=1e-9

def test_multi_register_wire_indices_and_snapshot_isolation():
    a,b=QuantumRegister(2,"a"),QuantumRegister(2,"b")
    raw=QuantumCircuit(a,b,global_phase=.51)
    raw.h(b[1]);raw.cx(b[1],a[0]);raw.ry(.2,b[0]);raw.z(a[1])
    # Strict logical import preserves gate semantics but may normalize register structure.
    c=q.from_qiskit(raw)
    baseline=OriginalCursor(c);candidate=IndexedCursor(c)
    first=candidate.at(0)
    initial=first.result.math.statevector()
    for index in (0,1,1,2,4):
        x,y=baseline.at(index),candidate.at(index)
        assert x.wires==y.wires and x.operation==y.operation
        x.result.test.state(y.result,ignore_global_phase=False).require()
    np.testing.assert_array_equal(first.result.math.statevector(),initial)
    exported=first.result.math.statevector();exported[:]=0
    np.testing.assert_array_equal(first.result.math.statevector(),initial)

def test_cursor_preflight_and_comparison(monkeypatch):
    monkeypatch.setattr(_trace,"_Cursor",IndexedCursor)
    c=q.Circuit(2).h(0).cx(0,1)
    ref=q.Circuit(2).h(0).z(1)
    assert c.debug.compare(ref,ignore_global_phase=False).step_index==2
    class Forbidden:
        def __init__(self,*a,**k):pytest.fail("budget must precede cursor creation")
    monkeypatch.setattr(_trace,"_Cursor",Forbidden)
    with pytest.raises(q.ResourceLimit):c.debug.trace(max_bytes=1)
    with pytest.raises(q.ResourceLimit):c.debug.trace(max_steps=1)
