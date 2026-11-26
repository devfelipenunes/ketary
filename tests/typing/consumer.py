from typing import Any, assert_type
import ketary as q
from numpy.typing import NDArray
import numpy as np

c = q.Circuit(2).gates.h(0).gates.cx(0, 1)
assert_type(c, q.Circuit)
r = c.run()
assert_type(r, q.Result)
assert_type(r.math.statevector(), NDArray[np.complex128])
assert_type(r.math.probabilities(), dict[str, float])
assert_type(r.sample(shots=10), dict[str, int])
assert_type(r.test.normalized(), q.CheckResult)
assert_type(c.debug.trace(), tuple[q.TraceStep, ...])
assert_type(c.resources.summary(), q.ResourceReport)
assert_type(q.Circuit.from_json(c.to_json()), q.Circuit)
# A strict consumer must reject these calls; unused ignores are failures.
c.gates.h("0")  # type: ignore[arg-type]
r.sample(shots="10")  # type: ignore[arg-type]
c.run(mode="hardware")  # type: ignore[arg-type]

assert_type(q.Circuit(2).h(0).cp(.2,0,1).copy(), q.Circuit)
assert_type(c.run(initial_state="01"), q.Result)
assert_type(r.math.density_matrix([0]), NDArray[np.complex128])
assert_type(r.math.purity([0]), float)
assert_type(q.qft(3), q.Circuit)
assert_type(r.sample(shots=10,wires=[0]), dict[str,int])

assert_type(q.Contract(2, expectations={"XX":1}).verify(r), q.VerificationReport)
assert_type(c.debug.checkpoint(1), q.TraceStep)
assert_type(r.math.top_probabilities(k=2), dict[str,float])

assert_type(q.Circuit(4).mcx([0,1,2],3),q.Circuit)
assert_type(q.phase_estimation(.125),q.Circuit)
assert_type(q.simon('101'),q.Circuit)

angle=q.Circuit.parameter('angle')
assert_type(q.Circuit.symbolic(2).rx(angle,0).bind({angle:.5}),q.Circuit)

assert_type(q.Circuit.classical(2,2).h(0).measure(0,0).if_x(1,0).measure(1,1),q.Circuit)
assert_type(q.teleportation(.3,.7),q.Circuit)

assert_type(c.visualize.svg(),str)
assert_type(r.visualize.bloch_svg(),str)

assert_type(q.recover_simon(['000','010','101'],3),str | None)

assert_type(r.math.observable_variance({'XX':.5,'ZZ':.5}),float)

assert_type(c.plan(bits=['00']),q.QueryPlan)
assert_type(q.StatisticalContract(2,probabilities={'00':.5}),q.StatisticalContract)

comparison=c.test.compare(q.bell())
assert_type(comparison,q.ComparisonReport)
assert_type(comparison.evidence,q.Evidence | None)
assert_type(c.h([0,1]).apply(q.bell(),wires=[0,1]),q.Circuit)
assert_type(c.register("input",[0,1]),tuple[int,...])
assert_type(r.math.expectation({0:"X",1:"Z"}),float)
assert_type(r.test.expectations({"XX":1}),q.VerificationReport)
assert_type(c.debug.verify_checkpoints({"bell":c.contract(expectations={"XX":1})}),q.DiagnosticReport)
assert_type(q.Circuit.symbolic(1).ry(angle,0).sweep(angle=[0,.5]).run(),tuple[q.Result,...])

decoded=q.decode_phase_estimation(q.phase_estimation(.25).run(),precision=3)
assert_type(decoded['phase'], Any)

assert_type(c.diff(q.bell()),q.SemanticDiffReport)
assert_type(c.diff(q.bell()).operator,q.OperatorMetricsReport)
assert_type(c.test.metrics(q.bell()).operator_norm,float | None)
assert_type(comparison.require(),q.ComparisonReport)

assert_type(r.verify(expectations={"XX":1}),q.SnapshotReport)
assert_type(c.test.external_equivalence(q.bell()),q.ExternalVerificationReport)
assert_type(c.debug.checkpoint("bell"),q.TraceStep)
assert_type(c.debug.compare_checkpoints(c,[("bell","bell")]),q.DiagnosticReport)
assert_type(q.decode_phase_estimation(q.phase_estimation(.25).run(),precision=3).phase,float | None)
assert_type(q.decode_bernstein_vazirani(q.bernstein_vazirani("101").run()).label,str | None)

H = .5*q.Z(0)+.8*(q.X(0)@q.X(1))
assert_type(H,q.Observable)
assert_type(H.to_dict(2),dict[str,float])
assert_type(r.math.expectation(H),float)
assert_type(r.math.variance(H),float)
assert_type(r.math.observable_variance_streamed(H),float)
assert_type(r.test.expectation(H,1.3),q.CheckResult)

assert_type(c.contract(expectations={H:1.3}),q.Contract)
assert_type(r.verify(expectations={H:1.3,"XX":1}),q.SnapshotReport)
assert_type(r.test.expectations({H:1.3}),q.VerificationReport)
assert_type(r.test.expectation(H,1.3).render(),str)
assert_type(c.contract(expectations={"XX":1}).verify(r).to_json(),str)

assert_type(c.apply(q.bell(),times=3),q.Circuit)
assert_type(c.apply_each(q.bell(),placements=[(0,1),(1,0)]),q.Circuit)
assert_type(c.repeat(2),q.Circuit)
assert_type(r.math.expectations([H,"XX",{0:"Z"}]),tuple[float,...])

assert_type(c.wires,range)
assert_type(q.chain(c.wires),tuple[tuple[int,int],...])
assert_type(q.ring(range(3)),tuple[tuple[int,int],...])
assert_type(q.star(c.wires),tuple[tuple[int,int],...])
assert_type(q.all_pairs(c.wires),tuple[tuple[int,int],...])
assert_type(c.ry([.1,.2],c.wires),q.Circuit)
assert_type(q.Circuit.symbolic(2).rz([angle,2*angle],[0,1]),q.Circuit)

assert_type(q.Circuit.classical(3,3).measure([2,0],[0,2]).reset(range(3)),q.Circuit)
