"""Required optional-extra CI; never silently skip missing Aer."""
import math
import pytest
import ketary as q
import qiskit_aer


def test_measurement_feedforward_reset_and_reproducibility():
    c=q.Circuit.classical(2,2).h(0).measure(0,0).if_x(1,0).measure(1,1)
    a=c.run_shots(shots=256,seed=42)
    b=c.run_shots(shots=256,seed=42)
    assert a.counts==b.counts and set(a.counts)=={"00","11"}
    assert sum(a.counts.values())==a.shots==256
    assert sum(a.probabilities().values())==pytest.approx(1)
    a.counts.clear()
    assert sum(a.counts.values())==256
    d=q.Circuit.classical(1,1).x(0).measure(0,0).reset(0).measure(0,0)
    assert d.run_shots(shots=32,seed=1).counts=={"0":32}
    e=q.Circuit.classical(1,1).measure(0,0).if_x(0,0,value=0).measure(0,0)
    assert e.run_shots(shots=32,seed=1).counts=={"1":32}


@pytest.mark.parametrize("theta,phi",[(0,0),(math.pi,0),(math.pi/2,0),
    (math.pi/2,math.pi/2),(.37,-.63),(2.1,.9)])
def test_teleportation_inverse_preparation(theta,phi):
    r=q.teleportation(theta,phi,verify=True).run_shots(shots=256,seed=42)
    assert set(r.counts)=={"000","001","010","011"}
    assert sum(r.counts.values())==256


def test_teleportation_computational_one():
    r=q.teleportation(math.pi,0).run_shots(shots=256,seed=42)
    assert all(label[0]=="1" for label in r.counts)
