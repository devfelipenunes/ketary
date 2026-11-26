"""Guard the API lifecycle registry and canonical parameter contracts."""
import json
from pathlib import Path
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/"docs"/name).read_text())
def test_lifecycle_complete_and_canonical_replacements():
    surface=read("api-surface.json")
    entries=read("api-lifecycle.json")["entries"]
    assert set(entries)=={name for group in surface.values() for name in group}
    expected={"Core":"canonical","Advanced":"supported_advanced","Native":"explicit_native","Compatibility":"retained_compatibility"}
    for category,names in surface.items():
        for name in names:
            entry=entries[name]
            assert entry["category"]==category
            assert entry["lifecycle"]==expected[category]
            assert entry["group"]
            if category=="Compatibility":
                assert entries[entry["prefer"]]["category"]!="Compatibility"
    assert entries["Circuit.apply"]["group"]=="composition"
    assert entries["Circuit.bind"]["group"]=="parameters"
    assert entries["Circuit.run"]["group"]=="execution"
    assert entries["Circuit.h"]["group"]=="gates"
    assert entries["Circuit.evolve"]["group"]=="composition"

def test_decision_rubric_and_retained_gate_evidence():
    policy=read("api-decisions.json")
    weights=policy["weights"]
    assert sum(weights.values())==100 and all(v>0 for v in weights.values())
    assert len({row["id"] for row in policy["candidates"]})==len(policy["candidates"])
    for row in policy["candidates"]:
        assert set(row["ratings"])==set(weights)
        assert set(row["gates"])==set(policy["gates"])
        assert all(v is None or type(v) is int and 0<=v<=2 for v in row["ratings"].values())
        assert all(v is None or type(v) is bool for v in row["gates"].values())
        assert row["evidence"] and row["rationale"]
        if row["decision"]=="retain":
            assert all(v is True for v in row["gates"].values())
        if any(v is None for v in row["ratings"].values()):
            assert row["decision"] not in ("promote",)
        if row["decision"]=="promote":
            assert all(v is True for v in row["gates"].values())
            assert sum(weights[k]*v/2 for k,v in row["ratings"].items())>=policy["thresholds"]["promote"]

def matrix(c):return Operator(c.to_qiskit()).data
def same(a,b):np.testing.assert_allclose(matrix(a),matrix(b),atol=1e-9,rtol=0)

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_parameter_identity_named_and_ordered_binding(seed):
    # Deliberately introduce parameters in reverse name order.
    z=q.Circuit.parameter("z");a=q.Circuit.parameter("a")
    c=q.Circuit.symbolic(3).ry([z,a],[2,0]).cp([z+a,a],pairs=[(2,1),(0,1)])
    rng=np.random.default_rng(seed);av,zv=rng.uniform(-1,1,2)
    original=c.to_qiskit()
    expected=q.Circuit(3).ry([zv,av],[2,0]).cp([zv+av,av],pairs=[(2,1),(0,1)])
    by_identity=c.bind({a:av,z:zv})
    by_name=c.bind(a=av,z=zv)
    by_order=c.bind([dict(a=av,z=zv)[p.name] for p in c.parameters])
    for v in (by_identity,by_name,by_order):same(v,expected)
    assert c.to_qiskit()==original and set(c.parameters)=={a,z}

def test_sweeps_are_independent_not_sequential_layers():
    a,b=q.Circuit.parameter_vector("t",2)
    template=q.Circuit.symbolic(2).ry([a,b],[0,1]).cx(0,1)
    rows=[[.2,.7],[-.4,.3]]
    expected=[template.bind(row) for row in rows]
    row_plan=template.sweep_rows(rows)
    columns={p.name:[row[i] for row in rows] for i,p in enumerate(template.parameters)}
    col_plan=template.sweep(**columns)
    rows[0][0]=99
    for plan in (row_plan,col_plan):
        for got,want in zip(plan.run(),expected,strict=True):
            np.testing.assert_allclose(got.math.statevector(),want.run().math.statevector(),atol=1e-9,rtol=0)
    sequential=q.Circuit(2)
    for c in expected:sequential.apply(c)
    assert not np.allclose(sequential.run().math.statevector(),expected[-1].run().math.statevector())
    assert set(template.parameters)=={a,b}

def test_bad_parameter_inputs_never_rename_or_partially_bind():
    a=q.Circuit.parameter("a");b=q.Circuit.parameter("b")
    c=q.Circuit.symbolic(2).rx(a,0).ry(b,1)
    before=c.to_qiskit()
    for bindings in ({a:.1},{q.Circuit.parameter("a"):.1,b:.2},[.1],[.1,float("nan")]):
        with pytest.raises(ValueError):c.bind(bindings)
    assert c.to_qiskit()==before
    with pytest.raises(ValueError):c.sweep_rows([[.1,.2],[.3]])
    with pytest.raises(ValueError):c.sweep(a=[.1,.2],b=[.3])
    with pytest.raises(q.UnsupportedOperation):c.evolve(q.X(0),time=.1)

def test_evolution_time_is_not_implicit_symbolic_binding():
    t=q.Circuit.parameter("t")
    c=q.Circuit(2)
    with pytest.raises((ValueError,TypeError)):c.evolve(q.Z(0)@q.Z(1),time=t)
    assert not c.to_qiskit().data

def test_apply_and_compose_are_not_aliases():
    a=q.Circuit(2).h(0);b=q.Circuit(2).cx(0,1)
    before=a.to_qiskit();independent=a.compose(b)
    assert a.to_qiskit()==before
    assert a.apply(b) is a
    same(a,independent)
