"""Independent analytic checks for bounded high-level Hamiltonians and oracles."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import SparsePauliOp, Operator


@pytest.mark.parametrize("n,edges,weights",[
    (3,[(0,1),(1,2)],[.3,2.]),
    (4,[(0,3),(1,2),(0,2)],[1.,-1.,2.]),
    (5,[(0,4),(1,3)],None),
])
def test_maxcut_diagonal_and_native_expectation(n,edges,weights):
    h=q.maxcut_hamiltonian(n,edges,weights=weights)
    w=weights or [1.]*len(edges)
    diagonal=[sum(v*((x>>a&1)!=(x>>b&1)) for (a,b),v in zip(edges,w,strict=True))
              for x in range(1<<n)]
    np.testing.assert_allclose(h.to_qiskit().to_matrix(),np.diag(diagonal),atol=1e-12,rtol=0)
    assert h.num_qubits==n
    c=q.Circuit(n).h(range(n)).ry(.23,0)
    state=c.run()
    assert state.math.expectation(h)==pytest.approx(np.dot(abs(state.math.statevector())**2,diagonal))


def test_native_observable_aggregate_and_roundtrip():
    native=SparsePauliOp.from_list([("IX",.2+1j),("ZZ",2),("IX",.3-1j),("YY",0)])
    h=q.Observable.from_qiskit(native)
    assert h.to_dict()=={"IX":.5,"ZZ":2.}
    np.testing.assert_allclose(native.to_matrix(),h.to_qiskit().to_matrix(),atol=1e-12,rtol=0)
    z=q.Observable.from_qiskit(SparsePauliOp.from_list([("ZZ",1),("ZZ",-1)]))
    assert z.num_qubits==2 and z.to_dict()=={"II":0.}
    with pytest.raises(ValueError):
        q.Observable.from_qiskit(SparsePauliOp.from_list([("X",1j)]))
    with pytest.raises(TypeError):
        q.Observable.from_qiskit("ZZ")


@pytest.mark.parametrize("n,marks",[(2,["00"]),(3,["001","110"]),(4,["1111","0000","0101"]),(6,["010101","111111"]),(8,["00110011"])])
def test_phase_oracle_strict_operator(n,marks):
    expected=np.ones(1<<n)
    for label in marks:
        expected[int(label,2)]=-1
    np.testing.assert_allclose(Operator(q.phase_oracle(marks).to_qiskit()).data,np.diag(expected),atol=1e-12,rtol=0)


@pytest.mark.parametrize("iterations",[0,1,2,3])
def test_amplification_strict_operator_and_probability(iterations):
    n=3
    marks=["001","110"]
    oracle=q.phase_oracle(marks)
    before=oracle.to_json()
    c=q.amplitude_amplification(oracle,iterations=iterations)
    size=1<<n
    h=1/np.sqrt(size)*np.array([[(-1)**((i&j).bit_count()) for j in range(size)] for i in range(size)])
    diagonal=np.ones(size)
    for label in marks:
        diagonal[int(label,2)]=-1
    diffusion=2*np.ones((size,size))/size-np.eye(size)
    expected=np.linalg.matrix_power(diffusion@np.diag(diagonal),iterations)@h
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-12,rtol=0)
    assert oracle.to_json()==before
    angle=np.arcsin(np.sqrt(len(marks)/size))
    probability=sum(c.run().math.probability(label) for label in marks)
    assert probability==pytest.approx(np.sin((2*iterations+1)*angle)**2)


@pytest.mark.parametrize("edges,weights",[
    ([],None),([(0,0)],None),([(0,3)],None),([(0,1),(1,0)],None),
    ([(0,1)],[1.,2.]), ([(0,1)],[float("nan")]), ({(0,1)},None)
])
def test_maxcut_rejects_invalid(edges,weights):
    with pytest.raises(ValueError):
        q.maxcut_hamiltonian(3,edges,weights=weights)


@pytest.mark.parametrize("marks",[[],["00","00"],["0"],["000","11"],["02"],{"00"},itertools.repeat("00")])
def test_oracle_rejects_invalid(marks):
    with pytest.raises(ValueError):
        q.phase_oracle(marks)


def test_amplification_rejects_nonbound_or_excessive():
    with pytest.raises(q.UnsupportedOperation):
        q.amplitude_amplification(q.Circuit.classical(2,2),iterations=1)
    with pytest.raises(q.ResourceLimit):
        q.amplitude_amplification(q.phase_oracle("00"),iterations=65)
