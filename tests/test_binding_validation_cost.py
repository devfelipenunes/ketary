import math
from types import SimpleNamespace
import numpy as np
import pytest
import ketary as q
from ketary._adapter import _validate_bound_values
from research.binding_validation_cost import previous,evaluate

@pytest.mark.parametrize("value",[0.,1.,-1.,np.float64(.3),2,float("nan"),float("inf"),True,np.bool_(False),1j,".3"])
def test_same_validation_semantics(value):
    item=SimpleNamespace(params=[value],operation=SimpleNamespace(params=[value]))
    raw=SimpleNamespace(parameters=(),data=[item],global_phase=0.)
    if isinstance(value,(bool,np.bool_,complex,str)) or not math.isfinite(float(value)):
        with pytest.raises(ValueError):previous(raw)
        with pytest.raises(ValueError):_validate_bound_values(raw)
    else:
        previous(raw);_validate_bound_values(raw)

def test_native_instruction_params_and_phase_validation():
    t=q.Circuit.parameter("t");c=q.Circuit.symbolic(2).ry(t,0).u(t,t*2,.3,1).cp(t,0,1).evolve(q.I(),time=t)
    raw=c.bind({t:.3}).to_qiskit()
    assert all(i.params==i.operation.params for i in raw.data)
    _validate_bound_values(raw)
    with pytest.raises(q.UnsupportedOperation):_validate_bound_values(c.to_qiskit())
    for phase in [float("nan"),float("inf")]:
        with pytest.raises(ValueError):_validate_bound_values(SimpleNamespace(parameters=(),data=[],global_phase=phase))
    with pytest.raises(ValueError):c.bind({t:float("nan")})

@pytest.mark.parametrize("n,layers",[(4,4),(8,16),(12,4)])
def test_paired_validation_cost(n,layers):
    row=evaluate(n,layers,reps=3)
    assert all(len(v["raw_ms"])==3 for v in row["stages"].values())
