import numpy as np
import pytest
import ketary as q
import ketary._execution as e
from qiskit.quantum_info import Statevector

def test_prepared_execution_validates_each_input_once(monkeypatch):
    c=q.Circuit(3).h(0).cx(0,2).ry(.37,1)
    v=np.arange(8)+1j*np.arange(8)[::-1]
    v=v/np.linalg.norm(v)
    snap=q.Result(v)
    inputs=[None,"110",v,snap,"001"]
    real=e.prepare_initial
    calls=[]
    def spy(n,s):
        calls.append(s);return real(n,s)
    monkeypatch.setattr(e,"prepare_initial",spy)
    out=c.run_many(inputs)
    assert len(calls)==len(inputs)
    for state,result in zip(inputs,out,strict=True):
        raw=c.to_qiskit()
        expected=(Statevector.from_instruction(raw) if state is None else
                  Statevector.from_label(state).evolve(raw) if type(state) is str else
                  Statevector(state.math.statevector() if isinstance(state,q.Result) else state).evolve(raw))
        np.testing.assert_allclose(result.math.statevector(),expected.data,atol=1e-9,rtol=0)
        assert not np.shares_memory(result._data,snap._data)
    v[:]=0
    assert np.isclose(np.linalg.norm(out[2]._data),1)

def test_invalid_prepared_batch_never_executes(monkeypatch):
    c=q.bell()
    def fail(*args,**kwargs):pytest.fail("evolution before all rows valid")
    monkeypatch.setattr(e,"execute_ideal",fail)
    with pytest.raises(ValueError):c.run_many(["00",[0,0,0,0]])
    with pytest.raises(q.ResourceLimit):c.run_many(["00","11"],max_bytes=319)
