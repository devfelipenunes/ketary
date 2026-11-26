import json
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from qiskit.circuit.library import MCXGate


@pytest.mark.parametrize("controls",[1,2,3,4,7])
def test_mcx_truth_table_and_replay(controls):
    c=q.Circuit(controls+1).mcx(range(controls),controls)
    expected=np.eye(1<<(controls+1))
    a=(1<<controls)-1
    b=(1<<(controls+1))-1
    expected[:,[a,b]]=expected[:,[b,a]]
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-12,rtol=0)
    c.test.equivalent(q.Circuit.from_json(c.to_json())).require()
    c.compose(c.inverse()).test.equivalent(q.Circuit(controls+1)).require()


def test_mcx_invalid_and_atomic():
    c=q.Circuit(9)
    for controls,target in [([],0),([0,0],1),(range(8),8),([0,1],1)]:
        with pytest.raises(ValueError):
            c.mcx(controls,target)
    assert c.inspect()["gate_count"]==0
    with pytest.raises(q.UnsupportedOperation):
        c.append(MCXGate(3,ctrl_state=0),[0,1,2,3])
    payload=json.loads(q.Circuit(4).mcx([0,1,2],3).to_json())
    payload["operations"][0]["wires"]=[0,1,2]
    with pytest.raises(ValueError):
        q.Circuit.from_json(json.dumps(payload))


@pytest.mark.parametrize("bits",["000","001","010","011","100","101","110","111"])
def test_exact_phase(bits):
    c=q.phase_estimation(int(bits,2)/8,3)
    p=c.run().math.marginal_probabilities([2,1,0])
    assert p[bits]==pytest.approx(1,abs=1e-12)


@pytest.mark.parametrize("secret",["1","10","101","111","0101"])
def test_simon_parity_support(secret):
    n=len(secret)
    p=q.simon(secret).run().math.marginal_probabilities(reversed(range(n)))
    mask=int(secret,2)
    for label,prob in p.items():
        expected=0 if (mask&int(label,2)).bit_count()%2 else 1/(1<<(n-1))
        assert prob==pytest.approx(expected,abs=1e-12)
