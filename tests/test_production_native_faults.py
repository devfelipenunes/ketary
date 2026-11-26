"""Production fault injection: errors must fail closed, even without Aer.

Synthetic backend results are not physical simulation or performance evidence.
"""
import itertools,sys,types
import numpy as np
import pytest
import ketary as q
import qiskit
from qiskit import QuantumCircuit,QuantumRegister,ClassicalRegister
from qiskit.quantum_info import DensityMatrix,Kraus,SparsePauliOp
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler.exceptions import TranspilerError

def native_multi():
    raw=QuantumCircuit(QuantumRegister(2),ClassicalRegister(1,"a"),ClassicalRegister(1,"b"))
    raw.measure([0,1],[0,1])
    return q.Circuit.from_dynamic(raw)

def fake_aer(monkeypatch,result):
    class Backend:
        def __init__(self,**kw):pass
        def run(self,*a,**kw):return self
        def result(self):return result
    fake=types.ModuleType("qiskit_aer")
    fake.AerSimulator=Backend
    noise=types.ModuleType("qiskit_aer.noise")
    noise.NoiseModel=type("NoiseModel",(),{})
    monkeypatch.setitem(sys.modules,"qiskit_aer",fake)
    monkeypatch.setitem(sys.modules,"qiskit_aer.noise",noise)
    monkeypatch.setattr(qiskit,"transpile",lambda circuit,**kw:circuit)
    monkeypatch.setattr(QuantumCircuit,"save_density_matrix",lambda self:None,raising=False)
    return noise.NoiseModel()

@pytest.mark.parametrize("counts",[None,{"01":8},{"0  1":8},{"0 x":8},{"0 1":0},{"0 1":True},{"0 1":7},{"00 1":8}])
def test_malformed_multiregister_counts(monkeypatch,counts):
    fake_aer(monkeypatch,types.SimpleNamespace(success=True,get_counts=lambda:counts))
    with pytest.raises(RuntimeError):native_multi().run_shots(shots=8)

def test_multiregister_success_schema(monkeypatch):
    fake_aer(monkeypatch,types.SimpleNamespace(success=True,get_counts=lambda:{"0 1":3,"1 0":5}))
    import importlib.metadata
    old=importlib.metadata.version
    monkeypatch.setattr(importlib.metadata,"version",lambda name:"test-fixture" if name=="qiskit-aer" else old(name))
    result=native_multi().run_shots(shots=8)
    assert result.counts=={"01":3,"10":5}
    assert result.probabilities()=={"01":.375,"10":.625}
    assert result.backend_version=="test-fixture"
    counts=result.counts;counts["01"]=0
    assert result.counts["01"]==3

@pytest.mark.parametrize("kind",["failed","bad_width","bad_trace","bad_psd","valid"])
def test_noisy_backend_result_fault(monkeypatch,kind):
    matrices={"bad_width":np.eye(4)/4,"bad_trace":np.eye(2),"bad_psd":np.diag([1.2,-.2]),"valid":np.diag([.25,.75])}
    result=types.SimpleNamespace(success=kind!="failed",data=lambda _:{"density_matrix":matrices[kind]})
    noise=fake_aer(monkeypatch,result)
    c=q.Circuit(1).x(0);before=c.to_qiskit()
    if kind=="valid":
        out=c.run_noisy(noise,seed=17)
        np.testing.assert_array_equal(out.data,matrices[kind])
        out.data[:]=0
        np.testing.assert_array_equal(matrices[kind],np.diag([.25,.75]))
    else:
        with pytest.raises(RuntimeError if kind=="failed" else ArithmeticError):c.run_noisy(noise,seed=17)
    assert c.to_qiskit()==before

def test_noisy_preflight_no_optional_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules,"qiskit_aer",None)
    with pytest.raises(q.UnsupportedOperation,match="dynamic"):q.Circuit(1).run_noisy(object())
    with pytest.raises(ValueError):q.Circuit(1).run_noisy(object(),seed=2**32)
    with pytest.raises(q.ResourceLimit):q.Circuit(1).run_noisy(object(),max_bytes=1)

def test_noisy_wrong_model(monkeypatch):
    fake_aer(monkeypatch,object())
    with pytest.raises(TypeError):q.Circuit(1).run_noisy(object())

def test_native_density_invalid_result(monkeypatch):
    monkeypatch.setattr(DensityMatrix,"from_instruction",lambda *a,**k:DensityMatrix(np.diag([1.2,-.2])))
    with pytest.raises(ArithmeticError):q.Circuit(1).run_density()

def test_channel_invalid_backend_result(monkeypatch):
    monkeypatch.setattr(DensityMatrix,"evolve",lambda *a,**k:DensityMatrix(np.diag([1.2,-.2])))
    with pytest.raises(ArithmeticError):q.Circuit(1).run_channel(Kraus([np.eye(2)]))

def test_channel_input_limits():
    with pytest.raises(q.UnsupportedOperation):q.Circuit(1).run_channel(Kraus([np.eye(2)/np.sqrt(17)]*17))
    bad=Kraus([np.eye(2)]);bad.data[0][0,0]=np.nan
    with pytest.raises(ValueError):q.Circuit(1).run_channel(bad)

def test_dynamic_full_register_condition(monkeypatch):
    raw=QuantumCircuit(2,2);raw.measure([0,1],[0,1])
    with raw.if_test((raw.cregs[0],2)) as otherwise:raw.x(0)
    with otherwise:raw.z(1)
    c=q.Circuit.from_dynamic(raw)
    assert c.to_qiskit()==raw
    raw=QuantumCircuit(1,1);raw.measure(0,0)
    with raw.if_test((raw.clbits[0],1)):
        with raw.if_test((raw.clbits[0],1)):
            with raw.if_test((raw.clbits[0],1)):
                with raw.if_test((raw.clbits[0],1)):raw.x(0)
    with pytest.raises(q.ResourceLimit,match="depth"):q.Circuit.from_dynamic(raw)

@pytest.mark.parametrize("mode",["logical","synthesized","target"])
def test_transpiler_failure_is_explicit(monkeypatch,mode):
    def fail(*a,**k):raise TranspilerError("injected native failure")
    monkeypatch.setattr(qiskit,"transpile",fail)
    c=q.bell();before=c.to_qiskit()
    with pytest.raises(q.UnsupportedOperation):
        if mode=="logical":c.transpile(basis_gates=["u","cx"])
        elif mode=="synthesized":q.Circuit.from_synthesized(before)
        else:c.transpile_for(GenericBackendV2(num_qubits=2,noise_info=False))
    assert c.to_qiskit()==before

def test_synthesis_wrong_operator_never_accepted(monkeypatch):
    raw=QuantumCircuit(1);raw.x(0)
    monkeypatch.setattr(qiskit,"transpile",lambda *a,**k:QuantumCircuit(1))
    with pytest.raises(q.UnsupportedOperation,match="residual"):q.Circuit.from_synthesized(raw)

def test_synthesis_noncanonical_output(monkeypatch):
    raw=QuantumCircuit(1);raw.x(0)
    monkeypatch.setattr(qiskit,"transpile",lambda *a,**k:raw.copy())
    with pytest.raises(q.UnsupportedOperation,match="noncanonical"):q.Circuit.from_synthesized(raw)

def test_synthesis_output_limit(monkeypatch):
    raw=QuantumCircuit(1);raw.h(0)
    too_many=QuantumCircuit(1)
    for _ in range(10001):too_many.u(0,0,0,0)
    monkeypatch.setattr(qiskit,"transpile",lambda *a,**k:too_many)
    with pytest.raises(q.ResourceLimit):q.Circuit.from_synthesized(raw)

@pytest.mark.parametrize("kw",[dict(num_clbits=13,probabilities={"0"*13:1}),dict(num_clbits=1,probabilities={"0":1},margin=0),dict(num_clbits=1,probabilities={"0":1},confidence=1)])
def test_statistical_contract_invalid(kw):
    with pytest.raises(ValueError):q.StatisticalContract(**kw)

def test_statistical_scope_and_width():
    c=q.StatisticalContract(1,probabilities={"0":1})
    with pytest.raises(TypeError):c.verify(object())
    with pytest.raises(ValueError):c.verify(q.ShotResult(8,2,0,(("00",8),),((1,0,0),(2,1,1))))
    assert c.verify(q.ShotResult(8,1,0,(("0",8),))).status=="UNSUPPORTED"

def test_observable_budgets():
    terms=lambda n:{"".join(p):1. for p in itertools.product("IXYZ",repeat=n)}
    a=q.Observable(terms(4));b=q.Observable(terms(3))
    with pytest.raises(q.ResourceLimit):a.product(b)
    with pytest.raises(q.ResourceLimit):q.Observable(terms(3)).on([0,1,2],width=63)
    left=q.Observable({p+"III":v for p,v in terms(3).items()})
    right=q.Observable({p:v for p,v in terms(3).items()})
    with pytest.raises(q.ResourceLimit):left.product(right)
    with pytest.raises(q.ResourceLimit):left@right
    with pytest.raises(TypeError):q.X(0)+object()
    with pytest.raises(TypeError):q.X(0)-object()
    with pytest.raises(TypeError):object()-q.X(0)
    with pytest.raises(TypeError):q.X(0)*object()
    with pytest.raises(TypeError):q.X(0)@object()

def test_checks_wrong_width_and_phase_flag():
    a=q.Circuit(1);b=q.Circuit(2)
    assert a.test.equivalent(b).status=="FAIL"
    with pytest.raises(ValueError):a.test.equivalent(a,ignore_global_phase=1)
    with pytest.raises(TypeError):a.test.metrics(object())
    with pytest.raises(ValueError):a.test.metrics(a,ignore_global_phase=1)

def test_native_complex_malformed_and_overflow(monkeypatch):
    r=q.Circuit(1).run();op=SparsePauliOp("I")
    with monkeypatch.context() as m:
        m.setattr(SparsePauliOp,"to_list",lambda self:[("bad",1.)])
        with pytest.raises(ValueError):r.math.expectation_complex(op)
    with monkeypatch.context() as m:
        m.setattr(SparsePauliOp,"to_list",lambda self:[("I",object())])
        with pytest.raises(ValueError):r.math.expectation_complex(op)
    with pytest.raises(ArithmeticError):r.math.expectation_complex(SparsePauliOp.from_list([("I",1e308),("I",1e308)]))
