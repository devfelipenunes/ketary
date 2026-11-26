import numpy as np
import pytest
from ketary import Result, ResourceLimit, _limit
BELL=np.array([1,0,0,1])/np.sqrt(2)
MINUS=np.array([1,0,0,-1])/np.sqrt(2)

def test_distribution_phase():
    a,b=Result(BELL),Result(MINUS)
    assert a.math.probabilities()==b.math.probabilities()
    assert a.math.fidelity(b)<1e-12
    assert a.test.fidelity(b).status=="FAIL"

def test_snapshot_isolation():
    a=BELL.copy(); r=Result(a); a[:]=0; exported=r.math.statevector(); exported[:]=0
    np.testing.assert_allclose(r.math.statevector(),BELL)

def test_sample():
    r=Result(BELL); a=r.sample(shots=1024,seed=42)
    assert a==r.sample(shots=1024,seed=42) and sum(a.values())==1024 and set(a)<={"00","11"}
    np.testing.assert_allclose(r.math.statevector(),BELL)

def test_global_phase():
    assert Result(BELL).math.fidelity(1j*BELL)>1-1e-12

def test_entanglement():
    assert Result(BELL).test.entangled(partition=([0],[1])).status=="PASS"
    assert Result([1,0,0,0]).test.entangled(partition=([0],[1])).status=="FAIL"

def test_checks():
    r=Result(BELL); r.test.normalized().require(); r.test.probability("00",.5).require()
    with pytest.raises(AssertionError): r.test.probability("00",1).require()
    with pytest.raises(TypeError): bool(r.test.normalized())

@pytest.mark.parametrize("bad",[[0,0],[1,1],[np.nan,0],[1,0,0]])
def test_bad_state(bad):
    with pytest.raises(ValueError): Result(bad)

def test_bad_parameters():
    r=Result(BELL)
    for bad in (0,True,1.5):
        with pytest.raises(ValueError): r.sample(shots=bad)
    with pytest.raises(ValueError): r.test.probability("00",.5,atol=np.nan)
    with pytest.raises(ValueError): r.math.entropy(([0],[0]))

def test_memory_guard():
    _limit(8,257,16*256*257)
    with pytest.raises(ResourceLimit): _limit(20,257,64*1024**2)
