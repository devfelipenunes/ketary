"""Reproducible bounded random circuits with independent native construction.

Record seed in test IDs. No formal proof or general random circuit support.
"""
from itertools import product
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector

SEEDS=(1101,2202,3303,4404,5505,6606)
def generated(n,seed,depth=24):
    rng=np.random.default_rng(seed)
    ketary=q.Circuit(n);native=QuantumCircuit(n)
    for _ in range(depth):
        gate=str(rng.choice(["h","x","s","sdg","rx","ry","rz","p","cx","cz","cp","rzz","ryy","rxx"]))
        if gate in ("cx","cz","cp","rzz","ryy","rxx"):
            a,b=map(int,rng.choice(n,size=2,replace=False))
            args=(a,b) if gate in ("cx","cz") else (float(rng.uniform(-np.pi,np.pi)),a,b)
        else:
            a=int(rng.integers(n));args=(a,) if gate in ("h","x","s","sdg") else (float(rng.uniform(-np.pi,np.pi)),a)
        getattr(ketary,gate)(*args);getattr(native,gate)(*args)
    phase=float(rng.uniform(-1,1))
    ketary.evolve(q.I(),time=-phase);native.global_phase=phase
    return ketary,native,rng

@pytest.mark.parametrize("n",[2,3,4])
@pytest.mark.parametrize("seed",SEEDS)
def test_random_circuit_strict_operator_and_replay(n,seed):
    c,raw,rng=generated(n,seed)
    ref=Operator(raw).data
    for candidate in (c,q.Circuit.from_json(c.to_json()),c.copy()):
        np.testing.assert_allclose(Operator(candidate.to_qiskit()).data,ref,rtol=0,atol=1e-9)
        v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
        state=candidate.run(initial_state=v)
        np.testing.assert_allclose(state.math.statevector(),Statevector(v).evolve(raw).data,rtol=0,atol=1e-9)
        assert state.math.norm()==pytest.approx(1,abs=1e-9)
        exported=state.math.statevector();exported[:]=0
        assert state.math.norm()==pytest.approx(1,abs=1e-9)
    inverse=c.copy().apply(c.inverse())
    np.testing.assert_allclose(Operator(inverse.to_qiskit()).data,np.eye(1<<n),rtol=0,atol=1e-9)

@pytest.mark.parametrize("seed",SEEDS)
def test_random_composition_order_and_observable_linearity(seed):
    c,raw,rng=generated(2,seed,depth=12)
    target=q.Circuit(4).h([0,1,2,3]);original=target.to_qiskit()
    wires=tuple(map(int,rng.choice(4,size=2,replace=False)))
    actual=target.copy().apply(c,wires=wires)
    reference=original.compose(raw,qubits=wires,inplace=False)
    np.testing.assert_allclose(Operator(actual.to_qiskit()).data,Operator(reference).data,atol=1e-9,rtol=0)
    assert target.to_qiskit()==original
    v=rng.normal(size=16)+1j*rng.normal(size=16);v/=np.linalg.norm(v)
    state=actual.run(initial_state=v)
    H=q.X(0)@q.Y(1);G=q.Z(0)+q.I()
    a,b=rng.uniform(-1,1,2)
    A=H.on(wires,width=4);B=G.on(wires,width=4)
    value=state.math.expectation(a*A+b*B)
    assert value==pytest.approx(a*state.math.expectation(A)+b*state.math.expectation(B),abs=1e-9)
    assert value==pytest.approx(float(Statevector(v).evolve(reference).expectation_value((a*A+b*B).to_qiskit(4)).real),abs=1e-9)

@pytest.mark.parametrize("seed",SEEDS)
def test_relative_phase_invisible_to_probabilities(seed):
    rng=np.random.default_rng(seed);t=float(rng.uniform(.2,1.2))
    good=q.Circuit(2).h(0).cx(0,1)
    bad=good.copy().p(t,0)
    p=good.run().math.probabilities();r=bad.run().math.probabilities()
    assert p.keys()==r.keys()
    assert all(p[k]==pytest.approx(r[k],abs=1e-9) for k in p)
    assert good.test.compare(bad).status=="FAIL"
    assert good.run().math.expectation("XX")==pytest.approx(1.,abs=1e-9)
    assert bad.run().math.expectation("XX")==pytest.approx(np.cos(t),abs=1e-9)
