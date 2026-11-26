import math
from fractions import Fraction
import numpy as np
import pytest
import ketary as q
from ketary._validation import _angle
from research.angle_validation_cost import previous_angle,evaluate

class FloatSubclass(float):
    def __float__(self):
        return 2.5

@pytest.mark.parametrize("value",[0.,-0.,.5,1e308,float("nan"),float("inf"),-float("inf"),1,2**10000,True,np.bool_(True),np.float64(.2),np.float32(.2),np.int64(3),Fraction(1,3),FloatSubclass(.3),"1",1j,None])
def test_angle_validation_preserves_previous_behavior(value):
    try:old=previous_angle(value)
    except ValueError as exc:
        with pytest.raises(ValueError) as err:_angle(value)
        assert str(err.value)==str(exc)
    else:
        new=_angle(value)
        assert type(new) is float and new==old
        assert math.copysign(1,new)==math.copysign(1,old)

def test_float_binding_and_global_phase_remain_finite():
    p=q.Circuit.parameter("p");c=q.Circuit.symbolic(2).ry(p,0).evolve(q.I(),time=p)
    for value in (float("nan"),float("inf"),-float("inf")):
        with pytest.raises(ValueError):c.bind({p:value})
        with pytest.raises(ValueError):q.Circuit(2).ry(value,0)
    assert c.bind({p:.2}).to_qiskit()==c.to_qiskit().assign_parameters({p:.2})

@pytest.mark.parametrize("n,count",[(2,16),(4,128),(8,512)])
def test_paired_angle_cost(n,count):
    row=evaluate(n,count,reps=2)
    assert all(len(v["raw_ms"])==2 for v in row["stages"].values())
