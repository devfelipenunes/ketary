import numpy as np
import pytest
import ketary as q
import qiskit
import qiskit.quantum_info as qi
from qiskit import QuantumCircuit
from ketary._transpilation import _synthesize_native

def test_rejected_lowering_evaluates_each_operator_once(monkeypatch):
    real=qi.Operator
    calls=[]
    def tracked(raw,*args,**kwargs):
        calls.append(raw)
        return real(raw,*args,**kwargs)
    monkeypatch.setattr(qi,"Operator",tracked)
    # Deliberately corrupt a native lowering, not an allowed approximate
    # result. The strict oracle must still reject it.
    def corrupt(*args,**kwargs):
        raw=QuantumCircuit(2);raw.u(.1,0,0,0)
        return raw
    monkeypatch.setattr(qiskit,"transpile",corrupt)
    source=QuantumCircuit(2);source.h(0);source.cx(0,1)
    with pytest.raises(q.UnsupportedOperation,match="strict synthesized operator residual"):
        _synthesize_native(source,seed=1101)
    assert len(calls)==2

def test_synthesis_preserves_complex_global_phase_and_ownership():
    raw=QuantumCircuit(2,global_phase=.37);raw.h(0);raw.cx(0,1);raw.ry(.41,1)
    got=_synthesize_native(raw,seed=1101)
    expected=qi.Operator(raw).data.copy()
    raw.x(0)
    np.testing.assert_allclose(qi.Operator(got.to_qiskit()).data,expected,atol=1e-9,rtol=0)
