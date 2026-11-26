import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from research.alpha_controlled_profile import source,reference,baseline,candidate,reduced,run


@pytest.mark.parametrize("state",[0,1])
@pytest.mark.parametrize("phase",[0.,-.73,.42])
@pytest.mark.parametrize("wires",[[],[0],[0,1,0],[2,2,1,1,0]])
def test_controlled_x_parity(state,phase,wires):
    c=source(3,wires,phase);before=c.to_qiskit()
    expected=reference(3,wires,phase,state)
    for fn in (baseline,candidate,reduced):
        actual=fn(c,state,1101)
        np.testing.assert_allclose(Operator(actual.to_qiskit()).data,expected,atol=1e-9,rtol=0)
        reverse=q.Circuit(4).apply(actual,wires=[3,2,1,0])
        p=[int(format(j,"04b")[::-1],2) for j in range(16)]
        np.testing.assert_allclose(Operator(reverse.to_qiskit()).data,expected[np.ix_(p,p)],atol=1e-9,rtol=0)
    assert c.to_qiskit()==before


def test_non_x_rejected():
    with pytest.raises(ValueError):reduced(q.Circuit(1).h(0),1,1101)


def test_profile_smoke():
    assert len(run(1101,1))==6
