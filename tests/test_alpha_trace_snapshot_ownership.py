import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from ketary._trace import _Cursor

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_trace_owned_checkpoints_match_prefix(seed):
    rng=np.random.default_rng(seed)
    raw=QuantumCircuit(4,global_phase=.37)
    for _ in range(6):
        raw.h(0);raw.id(3);raw.cx(0,2);raw.ry(float(rng.normal()),1);raw.rz(float(rng.normal()),2)
    c=q.Circuit.from_qiskit(raw)
    steps=c.debug.trace()
    arrays=[]
    for index,step in enumerate(steps):
        prefix=QuantumCircuit(4,global_phase=.37)
        for item in raw.data[:index]:
            prefix.append(item.operation,[raw.find_bit(w).index for w in item.qubits])
        np.testing.assert_allclose(step.result.math.statevector(),Statevector.from_instruction(prefix).data,atol=1e-9,rtol=0)
        assert not step.result._data.flags.writeable
        assert all(not np.shares_memory(step.result._data,a) for a in arrays)
        arrays.append(step.result._data)
    c.x(0)
    np.testing.assert_allclose(steps[-1].result.math.statevector(),Statevector.from_instruction(raw).data,atol=1e-9,rtol=0)

def test_repeated_cursor_checkpoint_is_independent():
    c=q.Circuit(2).h(0).cx(0,1)
    cursor=_Cursor(c)
    a=cursor.at(1).result
    b=cursor.at(1).result
    assert not np.shares_memory(a._data,b._data)
    before=a.math.statevector()
    cursor.at(2)
    np.testing.assert_array_equal(a.math.statevector(),before)
