"""Independent upstream contract probes, not Ketary product tests."""
import numpy as np
from qiskit import QuantumCircuit as QC
from qiskit.quantum_info import Statevector as SV, Operator as OP

def test_reference_bell_phase():
    plus=np.array([1,0,0,1],complex)/np.sqrt(2)
    minus=np.array([1,0,0,-1],complex)/np.sqrt(2)
    np.testing.assert_allclose(abs(plus)**2,abs(minus)**2,atol=1e-12)
    assert abs(np.vdot(plus,minus))**2<1e-12

def test_reference_trace_memory():
    assert (256+1)*16*2**8==1052672
    assert (256+1)*16*2**20==4311744512

def test_bell_and_ghz():
    for n in (2,3):
        qc=QC(n); qc.h(0)
        for i in range(n-1): qc.cx(i,i+1)
        ref=np.zeros(2**n,complex); ref[[0,-1]]=1/np.sqrt(2)
        np.testing.assert_allclose(SV.from_instruction(qc).data,ref,atol=1e-12)

def test_copy_isolation_supported_gates():
    qc=QC(2); qc.h(0); qc.cx(0,1)
    other=qc.copy(); other.z(0)
    assert len(qc.data)==2 and len(other.data)==3
    assert not SV.from_instruction(qc).equiv(SV.from_instruction(other))

def test_compose_order_and_nonmutation():
    a=QC(1); a.h(0); b=QC(1); b.z(0)
    ab=a.compose(b,inplace=False); ba=b.compose(a,inplace=False)
    assert len(a.data)==len(b.data)==1
    np.testing.assert_allclose(SV.from_instruction(ab).data,[2**-0.5,-2**-0.5],atol=1e-12)
    assert not SV.from_instruction(ab).equiv(SV.from_instruction(ba))

def test_decompose_preserves_operator_and_source():
    bell=QC(2); bell.h(0); bell.cx(0,1)
    qc=QC(2); qc.append(bell.to_gate(),[0,1]); expanded=qc.decompose()
    assert len(qc.data)==1 and len(expanded.data)==2
    np.testing.assert_allclose(OP(qc).data,OP(expanded).data,atol=1e-12)

def test_trace_wire_mapping_and_global_phase():
    qc=QC(3,global_phase=.37); qc.x(2); qc.h(0); qc.cx(2,1); qc.swap(0,2)
    state=SV.from_label("000")
    for ci in qc.data:
        state=state.evolve(ci.operation,qargs=[qc.find_bit(bit).index for bit in ci.qubits])
    np.testing.assert_allclose(np.exp(1j*float(qc.global_phase))*state.data,SV.from_instruction(qc).data,atol=1e-12)

def test_inverse_composition():
    qc=QC(2,global_phase=.21); qc.h(0); qc.cx(0,1); qc.z(1)
    np.testing.assert_allclose(OP(qc.compose(qc.inverse())).data,np.eye(4),atol=1e-12)

def test_controlled_global_phase():
    a=QC(1); b=QC(1,global_phase=np.pi)
    assert OP(a).equiv(OP(b))
    c=QC(2); c.h(0); c.append(a.to_gate().control(),[0,1])
    d=QC(2); d.h(0); d.append(b.to_gate().control(),[0,1])
    assert not SV.from_instruction(c).equiv(SV.from_instruction(d))

def test_deutsch_jozsa_two_inputs():
    for balanced in (False,True):
        qc=QC(3); qc.x(2); qc.h([0,1,2])
        if balanced: qc.cx(0,2)
        qc.h([0,1])
        probs=SV.from_instruction(qc).probabilities(qargs=[0,1])
        np.testing.assert_allclose(probs,[0,1,0,0] if balanced else [1,0,0,0],atol=1e-12)
