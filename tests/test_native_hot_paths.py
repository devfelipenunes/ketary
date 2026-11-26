"""Preserve public isolation and trusted binding/sweep semantics."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit import Gate

def test_public_input_and_export_defensive():
    a=np.array([1,0],dtype=complex)
    r=q.Result(a)
    a[:]=[0,1]
    export=r.math.statevector()
    export[:]=[0,1]
    assert r.math.probability("0")==1

@pytest.mark.parametrize("gate",["empty","h","swap","phase"])
def test_native_input_borrow_never_aliases(gate):
    data=np.array([1,2j,3,-4j],dtype=complex)
    data/=np.linalg.norm(data)
    r=q.Result(data)
    c=q.Circuit(2)
    if gate=="h": c.h(1)
    elif gate=="swap": c.swap(0,1)
    elif gate=="phase":
        native=QuantumCircuit(2,global_phase=.43)
        c=q.from_qiskit(native)
    expected=Statevector(data).evolve(c.to_qiskit()).data
    out=c.run(initial_state=r)
    np.testing.assert_allclose(out.math.statevector(),expected,atol=1e-12,rtol=0)
    np.testing.assert_array_equal(r.math.statevector(),data)
    assert not np.shares_memory(out._data,r._data)
    assert not out._data.flags.writeable
    assert not r._data.flags.writeable

def test_private_owned_output_and_alias_guard():
    a=np.array([1,0],dtype=complex)
    r=q.Result._from_evolution(a)
    assert r._data is a and not a.flags.writeable
    b=q.Result._from_evolution(r._data,borrowed=r._data)
    assert not np.shares_memory(b._data,r._data)
    owner=np.array([0,1,0,0],dtype=complex)
    view=owner[::2]
    view[:]=[1,0]
    r=q.Result._from_evolution(view)
    assert not np.shares_memory(r._data,owner)

def test_binding_trusted_expression_and_external_validation():
    a=q.Circuit.parameter("a")
    c=q.Circuit.symbolic(2).ry(a*2,0).cx(0,1).rz(a+1,1)
    native=c.to_qiskit()
    for v in [.1,-.8,2.]:
        assert c.bind([v]).to_qiskit()==native.assign_parameters({a:v})
    for v in [float("inf"),float("nan"),True]:
        with pytest.raises(ValueError): c.bind([v])
    external=QuantumCircuit(1)
    external.append(Gate("custom",1,[a]),[0])
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit.from_parameterized(external,{a:.1})

def test_sweep_no_json_and_independent_native_snapshots(monkeypatch):
    a=q.Circuit.parameter("a")
    c=q.Circuit.symbolic(2).ry(a,0).cx(0,1)
    expected=[c.bind([v]).run().math.statevector() for v in [0.,.3,1.]]
    def forbidden(*args,**kw): pytest.fail("JSON in native sweep hot path")
    monkeypatch.setattr(q.Circuit,"to_json",forbidden)
    monkeypatch.setattr(q.Circuit,"from_json",forbidden)
    plan=c.sweep_rows([[0.],[.3],[1.]])
    c.x(0)
    for _ in range(2):
        results=plan.run()
        for r,e in zip(results,expected,strict=True):
            np.testing.assert_allclose(r.math.statevector(),e,atol=1e-12,rtol=0)
    with pytest.raises(q.ResourceLimit): plan.run(max_bytes=255)

def test_selected_probabilities_unchanged():
    r=q.Circuit(3).h(0).ry(.4,2).run()
    labels=["111","001","100","000"]
    assert r.math.probabilities(bits=labels)=={label:r.math.probability(label) for label in labels}
