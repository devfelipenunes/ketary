import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.exceptions import CircuitError
from qiskit.quantum_info import Operator
from research.symbolic_suffix import suffix,evaluate

@pytest.mark.parametrize("failure",["injected","name_collision"])
@pytest.mark.parametrize("phase_only",[False,True])
def test_native_suffix_rollback_parameter_identity(failure,phase_only):
    p=Parameter("p");r=Parameter("r");raw=QuantumCircuit(3)
    raw.h(0)
    if phase_only:raw.global_phase=p
    else:raw.ry(p,1)
    before=raw.copy()
    def append(c):
        c.ry(r,0);c.rzz(p+r,0,2);c.cx(1,2)
        if failure=="injected":raise RuntimeError("after partial append")
        c.ry(Parameter("p"),2)
    with pytest.raises((RuntimeError,CircuitError)):suffix(raw,append)
    assert raw==before
    assert tuple(raw.parameters)==tuple(before.parameters)==(p,)
    assert raw.assign_parameters({p:.4})==before.assign_parameters({p:.4})
    raw.ry(r,0);before.ry(r,0)
    assert raw==before and set(raw.parameters)=={p,r}
    np.testing.assert_allclose(Operator(raw.assign_parameters({p:.3,r:.7})).data,
                               Operator(before.assign_parameters({p:.3,r:.7})).data,atol=1e-9,rtol=0)

@pytest.mark.parametrize("n,layers",[(4,4),(8,16),(12,4)])
def test_native_suffix_cost(n,layers):
    row=evaluate(n,layers,reps=3)
    assert row["gates"]==layers*(2*n-1)
