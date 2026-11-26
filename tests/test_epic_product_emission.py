import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from research.epic_product_profile import previous

@pytest.mark.parametrize("order",[1,2])
@pytest.mark.parametrize("steps",[1,3,16])
@pytest.mark.parametrize("time",[-.37,.0,.71])
def test_product_emission_preserves_order_and_strict_phase(order,steps,time):
    H=q.Observable({"III":.3,"XYZ":.9,"YII":-.4,"IZZ":.2,"ZZZ":-.7})
    c=q.Circuit(3).evolve_product(H,time=time,steps=steps,order=order)
    old=previous(3,H,time,steps,order)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(old.to_qiskit()).data,atol=1e-9,rtol=0)
    assert c.to_qiskit().count_ops()==old.to_qiskit().count_ops()

def test_product_invalid_late_angle_rollback():
    c=q.Circuit(3).h(0);before=c.to_qiskit()
    with pytest.raises(ValueError):
        c.evolve_product(q.Observable({"III":.2,"XYZ":1e308}),time=2.,steps=1,order=1)
    assert c.to_qiskit()==before
