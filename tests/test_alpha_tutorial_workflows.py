"""Executable qualification of the new tutorial workflows."""
import ketary as q

def test_tutorial_symbolic_sweep():
    theta=q.Circuit.parameter("theta")
    template=q.Circuit.symbolic(2).ry(theta,0).cx(0,1)
    results=template.sweep(theta=[0,.5,1]).run()
    assert len(results)==3
    for r in results:
        r.test.normalized().require()
        r.test.expectation(q.Z(0)@q.Z(1),1).require()

def test_tutorial_contract_and_replay():
    expected=q.bell()
    observed=expected.copy().z(0)
    contract=expected.contract(expectations={q.X(0)@q.X(1):1})
    contract.verify(expected.run()).require()
    assert contract.verify(observed.run()).status=="FAIL"
    q.Circuit.from_json(expected.to_json()).test.equivalent(expected).require()

def test_tutorial_bounded_inspection():
    c=q.Circuit(4).apply(q.bell(),wires=[3,1])
    assert len(c.inspect(start=0,limit=1)["operations"])==1
    assert c.resources.summary().gate_count==2
    r=c.run()
    assert abs(sum(r.math.marginal_probabilities([3,1]).values())-1)<1e-9
    assert len(r.math.top_probabilities(k=2))==2
