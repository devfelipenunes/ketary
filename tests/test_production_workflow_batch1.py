"""Distinct professional workflows and structural native preservation probes.

No native annotation support is inferred from equality of ideal statevectors.
"""
import io,itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit,QuantumRegister,qpy
from qiskit.quantum_info import Operator

def test_native_annotations_round_trip():
    raw=QuantumCircuit(QuantumRegister(2,"work"),name="experiment",metadata={"calibration":{"version":[1,2]},"purpose":"fence"})
    raw.h(0);raw.barrier(1,0);raw.cx(0,1);raw.global_phase=.31
    copied=raw.copy()
    assert copied.metadata==raw.metadata
    copied.metadata["calibration"]["version"].append(3)
    assert raw.metadata["calibration"]["version"]==[1,2]
    buf=io.BytesIO();qpy.dump(raw,buf);buf.seek(0)
    restored=qpy.load(buf)[0]
    assert restored.metadata==raw.metadata and restored.name==raw.name
    assert [(reg.name,len(reg)) for reg in restored.qregs]==[("work",2)]
    assert [(item.operation.name,tuple(restored.find_bit(w).index for w in item.qubits)) for item in restored.data]==[("h",(0,)),("barrier",(1,0)),("cx",(0,1))]
    assert restored.global_phase==pytest.approx(.31)
    np.testing.assert_allclose(Operator(restored).data,Operator(raw).data,atol=1e-9,rtol=0)
    with pytest.raises(q.UnsupportedOperation):q.from_qiskit(raw)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_synthesized(raw)

def test_barrier_is_structurally_distinct_from_identity():
    raw=QuantumCircuit(1);raw.h(0);raw.barrier();raw.h(0)
    np.testing.assert_allclose(Operator(raw).data,np.eye(2),atol=1e-9,rtol=0)
    assert len(raw.data)==3
    with pytest.raises(q.UnsupportedOperation):q.from_qiskit(raw)
    from qiskit import transpile
    optimized=transpile(raw,basis_gates=["h","u","cx"],optimization_level=1,seed_transpiler=1)
    assert [row.operation.name for row in optimized.data].count("barrier")==1
    assert len(optimized.data)>=3

def test_graph_cycle_stabilizers():
    c=q.Circuit(4).h(range(4))
    edges=[(0,1),(1,2),(2,3),(3,0)]
    for a,b in edges:c.cz(a,b)
    r=c.run()
    for i in range(4):
        H=q.X(i)@q.Z((i-1)%4)@q.Z((i+1)%4)
        r.test.expectation(H,1).require()
    # A phase defect violates its own stabilizer, yet leaves Z-basis distribution unchanged.
    bad=c.copy().z(1).run()
    assert bad.test.expectation(q.X(1)@q.Z(0)@q.Z(2),1).status=="FAIL"
    np.testing.assert_allclose(list(r.math.probabilities().values()),list(bad.math.probabilities().values()),atol=1e-9)

def test_dicke_weight_two():
    expected=np.array([1/np.sqrt(6) if i.bit_count()==2 else 0 for i in range(16)])
    c=q.Circuit.prepare_state(expected)
    r=c.run();np.testing.assert_allclose(r.math.statevector(),expected,atol=1e-9,rtol=0)
    assert sum(r.math.probability(format(i,"04b")) for i in range(16) if i.bit_count()!=2)<1e-9
    assert c.copy().z(0).run().test.state(expected).status=="FAIL"

def test_reversible_half_adder():
    c=q.Circuit(3).ccx(0,1,2).cx(0,1)
    U=Operator(c.to_qiskit()).data
    want=np.zeros((8,8))
    for x in range(8):
        a=x&1;b=(x>>1)&1;carry=(x>>2)&1
        y=a|((a^b)<<1)|((carry^(a&b))<<2)
        want[y,x]=1
    np.testing.assert_allclose(U,want,atol=1e-9,rtol=0)

def test_three_bit_modular_increment():
    c=q.Circuit(3).ccx(0,1,2).cx(0,1).x(0)
    want=np.zeros((8,8))
    for x in range(8):want[(x+1)%8,x]=1
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,want,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(c.inverse().to_qiskit()).data,want.T,atol=1e-9,rtol=0)

def test_ramsey_two_quadratures():
    phase=.73
    r=q.Circuit(1).h(0).rz(phase,0).run()
    np.testing.assert_allclose(r.math.expectations([q.X(0),q.Y(0)]),[np.cos(phase),np.sin(phase)],atol=1e-9,rtol=0)
    r.test.expectation(q.X(0),np.cos(phase)).require()

def test_spin_echo_refocusing():
    t=.83
    free=q.Circuit(1).h(0).rz(2*t,0).h(0).run()
    refocused=q.Circuit(1).h(0).rz(t,0).x(0).rz(t,0).x(0).h(0).run()
    assert free.math.probability("0")==pytest.approx(np.cos(t)**2)
    refocused.test.probability("0",1).require()

def test_chsh_quantum_correlation():
    r=q.bell().run()
    A0=q.Z(0);A1=q.X(0);B0=(q.Z(1)+q.X(1))*(1/np.sqrt(2));B1=(q.Z(1)-q.X(1))*(1/np.sqrt(2))
    S=(A0@B0)+(A0@B1)+(A1@B0)-(A1@B1)
    assert r.math.expectation(S)==pytest.approx(2*np.sqrt(2))
    assert q.Circuit(2).run().math.expectation(S)<2

def test_heisenberg_exchange():
    H=q.X(0)@q.X(1)+q.Y(0)@q.Y(1)+q.Z(0)@q.Z(1)
    t=.22
    swap=np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
    want=np.exp(1j*t)*(np.cos(2*t)*np.eye(4)-1j*np.sin(2*t)*swap)
    c=q.Circuit(2).evolve_exact(H,time=t)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,want,atol=1e-9,rtol=0)
    assert c.run(initial_state=[0,1,0,0]).math.probability("10")==pytest.approx(np.sin(2*t)**2)

def test_hamiltonian_ground_state_variational_scan():
    H=q.X(0)+.6*q.Z(0)
    p=q.Circuit.parameter("t");c=q.Circuit.symbolic(1).ry(p,0)
    theta=np.arctan2(-1.,-.6)
    r=c.bind({p:theta}).run()
    assert r.math.expectation(H)==pytest.approx(-np.sqrt(1+.6**2))
    np.testing.assert_allclose(c.expectation_jacobian({p:theta},[H]),[[0]],atol=1e-9)
    assert c.bind({p:theta+.3}).run().math.expectation(H)>r.math.expectation(H)

def test_repetition_code_coherent_recovery():
    theta=.57
    encode=q.Circuit(3).cx(0,1).cx(0,2)
    # Decode and correct the first bit with both syndrome bits as controls.
    recover=encode.inverse().ccx(1,2,0)
    for error in [None,0,1,2]:
        c=q.Circuit(3).ry(theta,0).apply(encode)
        if error is not None:c.x(error)
        c.apply(recover)
        rho=c.run().math.density_matrix([0])
        expected=np.array([np.cos(theta/2),np.sin(theta/2)])
        np.testing.assert_allclose(rho,np.outer(expected,expected),atol=1e-9,rtol=0)

def test_dephasing_channel_preserves_population():
    from qiskit.quantum_info import Kraus
    t=.38
    c=q.Circuit(1).ry(.7,0)
    rho=c.run_density().data
    out=c.run_channel(Kraus([np.sqrt(1-t)*np.eye(2),np.sqrt(t)*np.diag([1,-1])]))
    want=rho.copy();want[0,1]*=1-2*t;want[1,0]*=1-2*t
    np.testing.assert_allclose(out.data,want,atol=1e-9,rtol=0)

def test_mixed_basis_entanglement_witness():
    r=q.bell().run()
    witness=.5*q.I(1)-.25*(q.I(1)+q.X(0)@q.X(1)-q.Y(0)@q.Y(1)+q.Z(0)@q.Z(1))
    assert r.math.expectation(witness)==pytest.approx(-.5)
    assert q.Circuit(2).run().math.expectation(witness)==pytest.approx(0.)
