"""Analytic expectations for independently authored historical-pattern adaptations."""
import numpy as np
import pytest
import ketary as q
from math import pi

def test_bit_order_and_mutation():
    assert q.Circuit(3).x(2).run().math.probability("100")==1
    assert q.Circuit(3).x(0).run().math.probability("001")==1
    c=q.Circuit(3).x(0).ccx(0,1,2)
    fresh=q.Circuit(3).x(1).ccx(0,1,2)
    assert c.x(1).ccx(0,1,2).run().math.probability("111")==1
    assert fresh.run().math.probability("010")==1

def test_bell_target_and_fourier():
    uniform=q.Circuit(2).h(0).h(1).cx(0,1).run()
    assert list(uniform.math.probabilities().values())==pytest.approx([.25]*4)
    target=q.Circuit(2).h(0).x(1).cx(0,1).run()
    assert target.math.probability("01")==pytest.approx(.5)
    assert target.math.probability("10")==pytest.approx(.5)
    for inverse in (False,True):
        actual=q.qft(3,inverse=inverse).run(initial_state="001").math.statevector()
        np.testing.assert_allclose(actual,np.exp((-1 if inverse else 1)*2j*pi*np.arange(8)/8)/np.sqrt(8),atol=1e-12)

def test_ancilla_and_mapping():
    c=q.Circuit(5).ccx(0,1,3).ccx(2,3,4)
    assert c.run(initial_state="00111").math.probability("11111")==1
    assert c.ccx(0,1,3).run(initial_state="00111").math.probability("10111")==1
    small=q.Circuit(3).crz(pi/2,2,0).crz(pi/4,2,1)
    actual=q.Circuit(4).compose(small,wires=[2,3,0])
    expected=q.Circuit(4).crz(pi/2,0,2).crz(pi/4,0,3)
    assert actual.test.metrics(expected)["status"]=="PASS"
    assert actual.run(initial_state="0001").math.amplitude("0001")==pytest.approx(np.exp(-3j*pi/8))
