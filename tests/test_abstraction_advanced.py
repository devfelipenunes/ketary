"""Analytic and dynamic controls for advanced research patterns."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from research import abstraction_advanced as a
from research import abstraction_primitives as p

def matrix(c):return Operator(c.to_qiskit()).data
def same(a,b):np.testing.assert_allclose(a,b,atol=1e-9,rtol=0)

@pytest.mark.parametrize("seed",[1101,2202,3303])
@pytest.mark.parametrize("n",[1,2,3])
def test_amplitude_preparation_preserves_complex_phase(seed,n):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    c=a.amplitude_preparation(v)
    same(c.run().math.statevector(),v)
    m=matrix(c);same(m.conj().T@m,np.eye(1<<n))

def test_product_state_order():
    rows=[(.2,.3),(-.7,.4),(.5,-.8)]
    v=np.array([1.])
    for theta,phi in reversed(rows):
        v=np.kron(v,[np.exp(-.5j*phi)*np.cos(theta/2),np.exp(.5j*phi)*np.sin(theta/2)])
    same(a.product_state(rows).run().math.statevector(),v)

@pytest.mark.parametrize("bad",[[1,1],[0,0],[1,0,0],[float("nan"),0]])
def test_invalid_preparation(bad):
    with pytest.raises(ValueError):a.amplitude_preparation(bad)

@pytest.mark.parametrize("n,labels",[(1,["0"]),(2,["00","11"]),(3,["000","101","111"]),(3,[])])
def test_truth_oracle_every_target_input(n,labels):
    c=a.truth_oracle(n,labels);N=1<<n;ref=np.zeros((2*N,2*N))
    for i in range(2*N):
        f=int(format(i%N,f"0{n}b") in labels)
        ref[i^(f*N),i]=1
    same(matrix(c),ref)

@pytest.mark.parametrize("n",[1,2,3,4])
def test_adder_every_input(n):
    N=1<<n;expected=np.zeros((N*N,N*N))
    for x in range(N*N):
        aa,bb=x%N,x//N
        expected[aa+N*((aa+bb)%N),x]=1
    same(matrix(a.add_register(n)),expected)

def test_amplification_known_marked_state_and_sign():
    u=q.Circuit(2).h([0,1]);oracle=q.phase_oracle("10")
    out=a.amplify(u,oracle,1)
    same(out.run().math.statevector(),np.eye(4)[2])
    same(matrix(a.amplify(u,oracle,0)),matrix(u))

def test_controlled_power_relative_phase_and_native_gate_fast_path():
    native=QuantumCircuit(1,global_phase=.37);native.rx(.19,0)
    b=q.from_qiskit(native);out=a.controlled_power(b,3)
    ref=np.eye(4,dtype=complex);ref[np.ix_([1,3],[1,3])]=np.linalg.matrix_power(matrix(b),3)
    same(matrix(out),ref)
    assert len(p.controlled(q.Circuit(1).p(.37,0)).to_qiskit().data)==1
    assert len(p.evolve(q.Z(0)@q.Z(1)+q.Z(1)@q.Z(2),.3).to_qiskit().data)==2
    assert len(p.evolve(sum(q.X(i) for i in range(3)),.2).to_qiskit().data)==3

def test_uncompute_ancilla_contract_clean_and_dirty():
    c=a.explicit_uncompute_parity(4,[0,1],2,3)
    expected=np.zeros((16,16))
    for i in range(16):
        bit=((i&1)^((i>>1)&1)^((i>>2)&1))
        expected[i^(bit<<3),i]=1
    same(matrix(c),expected)
    # A dirty ancilla is restored, but changes the target relative to clean input.
    same(c.run(initial_state="0100").math.statevector(),np.eye(16)[12])
    same(c.run(initial_state="0000").math.statevector(),np.eye(16)[0])
    with pytest.raises(ValueError):a.explicit_uncompute_parity(4,[0,1],2,2)

@pytest.mark.parametrize("fault,expected",[(None,"00"),(0,"01"),(1,"11"),(2,"10")])
def test_phase_syndrome(fault,expected):
    pytest.importorskip("qiskit_aer")
    assert a.syndrome_phase_flip(fault).run_shots(shots=32,seed=1201).counts=={expected:32}

@pytest.mark.parametrize("value,expected",[(1,"111"),(0,"001")])
def test_conditional_sequence(value,expected):
    pytest.importorskip("qiskit_aer")
    out=a.conditional_sequence(0,value,[("x",1),("x",2)])
    assert out.run_shots(shots=32,seed=1201).counts=={expected:32}
