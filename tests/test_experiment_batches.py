"""Explicit experiment batches, native equivalence and preflight."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Statevector


def test_run_many_native_complex_inputs_and_order():
    c=q.Circuit(3).h(0).cx(0,2).ry(.3,1)
    vector=np.arange(8)+1j*np.arange(8)[::-1]
    vector=vector/np.linalg.norm(vector)
    snapshot=q.Circuit(3).x(1).run()
    inputs=[None,"110",vector,snapshot,"000"]
    results=c.run_many(iter(inputs))
    assert len(results)==len(inputs)
    for state,result in zip(inputs,results,strict=True):
        if state is None:
            expected=Statevector.from_instruction(c.to_qiskit())
        else:
            source=(Statevector.from_label(state) if isinstance(state,str) else
                    Statevector(state.math.statevector() if isinstance(state,q.Result) else state))
            expected=source.evolve(c.to_qiskit())
        np.testing.assert_allclose(result.math.statevector(),expected.data,atol=1e-12,rtol=0)
    assert results[0] is not results[-1]


def test_run_many_preflight_before_execution(monkeypatch):
    import ketary._execution as e
    c=q.bell()
    def forbidden(*a,**k):
        pytest.fail("native evolution before batch preflight")
    monkeypatch.setattr(e,"execute_ideal",forbidden)
    for inputs in [["00","x0"],["00",[1,0]],["00",[0,0,0,0]],[],itertools.repeat("00"),{"00"}]:
        with pytest.raises(ValueError):
            c.run_many(inputs)
    with pytest.raises(q.ResourceLimit):
        c.run_many(["00","11"],max_bytes=319)
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit.classical(2,2).run_many(["00"])


def test_sweep_rows_matches_native_and_existing_zipped_plan():
    a,b=q.Circuit.parameter("a"),q.Circuit.parameter("b")
    c=q.Circuit.symbolic(2).ry(b,0).rx(a,1).cx(0,1)
    rows=[(.1,.2),(.4,.8),(.5,.7)]
    plan=c.sweep_rows(iter(rows))
    assert plan.bindings==tuple({"a":a,"b":b} for a,b in rows)
    zipped=c.sweep(a=[r[0] for r in rows],b=[r[1] for r in rows])
    for result,old,row in zip(plan.run(),zipped.run(),rows,strict=True):
        native=Statevector.from_instruction(c.to_qiskit().assign_parameters(list(row)))
        np.testing.assert_allclose(result.math.statevector(),native.data,atol=1e-12,rtol=0)
        np.testing.assert_allclose(result.math.statevector(),old.math.statevector(),atol=1e-12,rtol=0)
    c.h(0)
    assert plan.bindings==zipped.bindings


@pytest.mark.parametrize("rows",[[],[[.1,.2]],[[float("nan")]],[[.1],[]],{"a":[.1]},itertools.repeat([.1])])
def test_sweep_rows_preflight(rows):
    a=q.Circuit.parameter("a")
    with pytest.raises(ValueError):
        q.Circuit.symbolic(1).ry(a,0).sweep_rows(rows)


def test_selected_probabilities_avoid_full_enumeration():
    r=q.ghz(17).run()
    labels=["1"*17,"0"*17,"0"*16+"1"]
    with pytest.raises(q.ResourceLimit):
        r.math.probabilities()
    p=r.math.probabilities(bits=labels,max_outcomes=3)
    assert list(p)==labels
    assert p==pytest.approx({labels[0]:.5,labels[1]:.5,labels[2]:0})
    for invalid in [[],["0"*17]*2,["00"],"0"*17,{"0"*17}]:
        with pytest.raises(ValueError):
            r.math.probabilities(bits=invalid)
    with pytest.raises(q.ResourceLimit):
        r.math.probabilities(bits=labels,max_outcomes=2)
