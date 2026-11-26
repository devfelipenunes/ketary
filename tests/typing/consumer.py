from typing import assert_type
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
