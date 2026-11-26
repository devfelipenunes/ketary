import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit,QuantumRegister,ClassicalRegister
from qiskit.quantum_info import DensityMatrix
from qiskit.providers.fake_provider import GenericBackendV2

def test_density_mixed_state_and_independence():
    rho=np.array([[.7,.1j],[-.1j,.3]])
    initial=DensityMatrix(rho.copy())
    c=q.Circuit(1).h(0)
    H=np.array([[1,1],[1,-1]])/np.sqrt(2)
    out=c.run_density(initial)
    np.testing.assert_allclose(out.data,H@rho@H.conj().T,atol=1e-9,rtol=0)
    out.data[:]=0
    np.testing.assert_allclose(initial.data,rho,atol=1e-9,rtol=0)
    np.testing.assert_allclose(q.bell().run_density().data,np.outer([1,0,0,1],[1,0,0,1])/2,atol=1e-9,rtol=0)
    with pytest.raises(q.ResourceLimit):c.run_density(max_bytes=191)
    with pytest.raises(ValueError):c.run_density(DensityMatrix(np.diag([1.2,-.2])))
    with pytest.raises(q.UnsupportedOperation):q.Circuit.classical(1,1).run_density()

def test_dynamic_import_register_order():
    raw=QuantumCircuit(QuantumRegister(2),ClassicalRegister(1,"a"),ClassicalRegister(1,"b"))
    raw.x(0);raw.measure(0,0)
    with raw.if_test((raw.clbits[0],1)):
        raw.h(1);raw.h(1);raw.x(1)
    raw.measure(1,1)
    c=q.Circuit.from_dynamic(raw)
    assert c.to_qiskit()==raw
    raw.x(0);assert c.to_qiskit()!=raw
    with pytest.raises(q.UnsupportedOperation):c.run()

def test_dynamic_rejects_nested_measure_and_unbound():
    raw=QuantumCircuit(1,1)
    with raw.if_test((raw.clbits[0],1)):raw.measure(0,0)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_dynamic(raw)
    raw=QuantumCircuit(1,1);raw.ry(q.Circuit.parameter("t"),0)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_dynamic(raw)

def test_target_transpilation_no_submission(monkeypatch):
    backend=GenericBackendV2(num_qubits=3,basis_gates=["id","rz","sx","x","cx"],seed=17)
    monkeypatch.setattr(backend,"run",lambda *a,**k:pytest.fail("unexpected submission"))
    c=q.bell();raw=c.transpile_for(backend,seed=17)
    assert isinstance(raw,QuantumCircuit) and raw.layout is not None
    assert set(row.operation.name for row in raw.data)<={"id","rz","sx","x","cx"}
    assert c.num_qubits==2

def test_dynamic_multiple_register_shots():
    pytest.importorskip("qiskit_aer")
    raw=QuantumCircuit(QuantumRegister(2),ClassicalRegister(1,"a"),ClassicalRegister(1,"b"))
    raw.x(0);raw.measure(0,0)
    with raw.if_test((raw.clbits[0],1)):raw.x(1)
    raw.measure(1,1)
    result=q.Circuit.from_dynamic(raw).run_shots(shots=32,seed=17)
    assert result.counts=={"11":32} and result.measured_bits==(0,1)
    # Asymmetric labels distinguish bit order from count-total checks.
    raw=QuantumCircuit(QuantumRegister(2),ClassicalRegister(1,"a"),ClassicalRegister(1,"b"))
    raw.x(0);raw.measure([0,1],[0,1])
    assert q.Circuit.from_dynamic(raw).run_shots(shots=16,seed=17).counts=={"01":16}

def test_noisy_density_analytic_bit_flip():
    pytest.importorskip("qiskit_aer")
    from qiskit_aer.noise import NoiseModel,pauli_error
    noise=NoiseModel();noise.add_all_qubit_quantum_error(pauli_error([("X",.2),("I",.8)]),["x"])
    c=q.Circuit(1).x(0)
    np.testing.assert_allclose(c.run_noisy(noise,seed=1).data,np.diag([.2,.8]),atol=1e-9,rtol=0)
    with pytest.raises(TypeError):c.run_noisy(object())


def test_native_target_sampler_workflow():
    # Local fake backend only. This qualifies the native handoff, not hardware.
    from qiskit.primitives import BackendSamplerV2
    backend=GenericBackendV2(num_qubits=2,basis_gates=["id","rz","sx","x","cx"],seed=11,noise_info=False)
    c=q.Circuit.classical(2,2).x(0).measure([0,1],[0,1])
    compiled=c.transpile_for(backend,seed=11)
    sampler=BackendSamplerV2(backend=backend,options={"seed_simulator":11})
    result=sampler.run([compiled],shots=16).result()
    assert result[0].data.c.get_counts()=={"01":16}

@pytest.mark.parametrize("bad",[None,object()])
def test_dynamic_input_type(bad):
    with pytest.raises(TypeError):q.Circuit.from_dynamic(bad)

def test_dynamic_limits_and_register_partition():
    from qiskit.circuit import Clbit
    with pytest.raises(q.ResourceLimit):q.Circuit.from_dynamic(QuantumCircuit(13,1))
    raw=QuantumCircuit(1)
    raw.add_bits([Clbit()])
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_dynamic(raw)
    raw=QuantumCircuit(1,1);raw.metadata={"experiment":1}
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_dynamic(raw)
    raw=QuantumCircuit(1,1);raw.barrier()
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_dynamic(raw)

def test_density_and_target_limits():
    c=q.Circuit(1)
    with pytest.raises(TypeError):c.run_density(np.eye(2)/2)
    with pytest.raises(ValueError):c.run_density(DensityMatrix(np.eye(4)/4))
    with pytest.raises(q.ResourceLimit):q.Circuit(9).run_density()
    with pytest.raises(TypeError):c.transpile_for(object())
    b=GenericBackendV2(num_qubits=2,noise_info=False)
    with pytest.raises(ValueError):c.transpile_for(b,optimization_level=4)
    with pytest.raises(q.ResourceLimit):q.Circuit(3).transpile_for(b)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.symbolic(1).ry(q.Circuit.parameter("t"),0).transpile_for(b)
