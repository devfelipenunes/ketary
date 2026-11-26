"""Native identity, expression, phase and retained-row ownership qualification."""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q

@pytest.mark.parametrize("seed",[713,2909,8017])
def test_complete_partial_named_and_row_binding(seed):
    rng=np.random.default_rng(seed)
    a,b=q.Circuit.parameter_vector("angle",2)
    raw=QuantumCircuit(3,global_phase=a/3-b/7)
    raw.ry(a+b,2);raw.cx(2,0);raw.rz(2*a-b,0);raw.ry(a,1)
    c=q.Circuit.from_symbolic(raw)
    original=c.to_qiskit()
    rows=[tuple(float(v) for v in rng.uniform(-2,2,2)) for _ in range(8)]
    plan=c.sweep_rows(rows)
    named=c.sweep(**{p.name:[row[i] for row in rows] for i,p in enumerate(c.parameters)})
    for i,row in enumerate(rows):
        mapping=dict(zip(c.parameters,row,strict=True))
        reference=raw.assign_parameters(mapping)
        partial=c.bind_partial({a:mapping[a]})
        assert partial.parameters==(b,)
        variants=(c.bind(mapping),c.bind(row),c.bind(**{p.name:v for p,v in mapping.items()}),
                  partial.bind({b:mapping[b]}),plan._payloads[i],named._payloads[i])
        for candidate in variants:
            assert candidate.to_qiskit()==reference
            np.testing.assert_allclose(Operator(candidate.to_qiskit()).data,Operator(reference).data,atol=1e-9,rtol=0)
    assert c.to_qiskit()==original
    saved=plan._payloads[1].to_qiskit()
    plan._payloads[0].x(0)
    assert plan._payloads[1].to_qiskit()==saved
    assert c.to_qiskit()==original
    c.h(1)
    assert plan._payloads[1].to_qiskit()==saved
    snapshot=plan.bindings
    snapshot[0][a.name]=999.
    assert plan.bindings[0][a.name]!=999.

def test_same_name_is_not_same_identity():
    a=q.Circuit.parameter("theta")
    other=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(a,0)
    before=c.to_qiskit()
    with pytest.raises(ValueError):c.bind({other:.2})
    with pytest.raises(ValueError):c.bind_partial({other:.2})
    with pytest.raises(ValueError):c.bind({a:.2},theta=.2)
    assert c.to_qiskit()==before
    assert c.bind(theta=.2).to_qiskit()==c.bind({a:.2}).to_qiskit()

@pytest.mark.parametrize("bad",[float("nan"),float("inf"),True,1+2j])
def test_invalid_late_sweep_row_rejected_before_assignment(bad,monkeypatch):
    p=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(p,0)
    before=c.to_qiskit()
    def fail(*args,**kwargs):pytest.fail("native binding before all rows admitted")
    monkeypatch.setattr(q.Circuit,"_bind_numeric",fail)
    with pytest.raises(ValueError):c.sweep_rows([(.2,),(bad,)])
    assert c.to_qiskit()==before

def test_expression_failure_and_unbound_rejection():
    p=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(1/p,0)
    before=c.to_qiskit()
    with pytest.raises(ValueError):c.bind({p:0.})
    with pytest.raises(ValueError):c.sweep_rows([(.2,),(0.,)])
    with pytest.raises(q.UnsupportedOperation):c.run()
    with pytest.raises(q.UnsupportedOperation):c.to_json()
    assert c.to_qiskit()==before
    np.testing.assert_allclose(Operator(c.bind({p:2.}).to_qiskit()).data,Operator(q.Circuit(2).ry(.5,0).to_qiskit()).data,atol=1e-9,rtol=0)
