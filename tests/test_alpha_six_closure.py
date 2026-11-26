"""Bounded closure profiles and negative controls."""
import numpy as np
import pytest
import ketary as q
from research.alpha_six_unitary import cases,evaluate
from research.alpha_six_variational import evaluate as var_evaluate
from research.alpha_six_verification import evaluate as verify_evaluate
from research.abstraction_advanced import truth_oracle,amplify

@pytest.mark.parametrize("index",range(8))
def test_unitary_profile(index):
    row=evaluate(list(cases(1101))[index],1101,reps=1)
    assert set(row["paths"])=={"ketary","qiskit"}
    assert all(len(p["run"]["raw_ms"])==1 for p in row["paths"].values())

@pytest.mark.parametrize("kind",["spin","excited","overlap","multi"])
def test_variational_profile(kind):
    row=var_evaluate(kind,1101,reps=1)
    assert all(abs(p["histories"][0]["final"]-row["minimum"])<1e-7 for p in row["paths"].values())

@pytest.mark.parametrize("kind",["phase","reversible"])
def test_verification_profile(kind):
    row=verify_evaluate(kind,2,1101,reps=1)
    assert all(p["payload_bytes"][0]>0 for p in row["paths"].values())

def test_existing_oracle_and_amplification_bounds():
    for invalid in (["01","01"],["0","11"],["0x"]):
        with pytest.raises(ValueError):q.phase_oracle(invalid)
    with pytest.raises(ValueError):q.parity_oracle("000")
    with pytest.raises(q.ResourceLimit):truth_oracle(4,[])
    with pytest.raises(q.ResourceLimit):q.amplitude_amplification(q.phase_oracle("00"),iterations=65)
    with pytest.raises(ValueError):amplify(q.Circuit(2),q.phase_oracle("000"),1)

def test_dense_preparation_contract():
    with pytest.raises(ValueError):q.Circuit.prepare_state([1,1])
    with pytest.raises(ValueError):q.Circuit.prepare_state([complex(0,float("nan")),0])
    with pytest.raises(q.ResourceLimit):q.Circuit.prepare_state(np.ones(64)/8)
