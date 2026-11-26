"""CH14: preserve row and column sweep contracts while eliminating reparse."""
import itertools
import numpy as np
import pytest
import ketary as q

@pytest.mark.parametrize("n",[2,4,6])
@pytest.mark.parametrize("count",[1,8,32])
def test_rows_and_columns_match(n,count):
    p=q.Circuit.parameter_vector("t",n)
    c=q.Circuit.symbolic(n).ry(p,range(n)).cx(pairs=q.chain(range(n)))
    rng=np.random.default_rng(1101);rows=rng.uniform(-1,1,(count,n)).tolist()
    column=c.sweep(**{x.name:[row[i] for row in rows] for i,x in enumerate(c.parameters)})
    direct=c.sweep_rows(iter(iter(row) for row in rows))
    assert direct.bindings==column.bindings
    assert list(direct.bindings[0])==[x.name for x in c.parameters]
    rows[0][0]=99.
    assert direct.bindings==column.bindings
    for a,b in zip(direct.run(),column.run(),strict=True):
        np.testing.assert_allclose(a.math.statevector(),b.math.statevector(),atol=1e-9,rtol=0)

@pytest.mark.parametrize("rows",[[[.1,.2],[.3]],[[.1,.2],[.3,float("nan")]],[[.1,.2],[.3,True]],[],[[.1,.2]]*33])
def test_preflight_before_binding(rows,monkeypatch):
    a,b=q.Circuit.parameter_vector("t",2);c=q.Circuit.symbolic(2).ry([a,b],[0,1])
    before=c.to_qiskit()
    monkeypatch.setattr(q.Circuit,"bind",lambda *a,**k:pytest.fail("binding before full validation"))
    with pytest.raises(ValueError):c.sweep_rows(rows)
    assert c.to_qiskit()==before

def test_bounded_generator_and_defensive_bindings():
    a,b=q.Circuit.parameter_vector("t",2);c=q.Circuit.symbolic(2).ry([a,b],[0,1])
    seen=[]
    def infinite():
        while True:
            seen.append(1);yield [.1,.2]
    with pytest.raises(q.ResourceLimit):c.sweep_rows(infinite())
    assert len(seen)==33
    plan=c.sweep_rows([[.1,.2]])
    before=plan.bindings
    exported=plan.bindings;exported[0][a.name]=3.
    assert plan.bindings==before
