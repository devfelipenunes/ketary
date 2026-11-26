# Generated mathematical qualification — 1,000 cases

Four disjoint seed namespaces, 250 generated cases each: complex state/Born/
Pauli/reduced-density math (including near-basis states); ordered gates and
inverse/replay with independent dense matrices; complex Pauli algebra and
variance; nonlinear shared-parameter Jacobian/Hessian/QGT against closed
form. All expected results are independently constructed from NumPy scalar
and matrix formulas, not Qiskit circuit execution. Each pytest node contains
its replayable seed; run the exact node and reduce the recorded generated
width/gate count/parameters manually when diagnosing. No automatic shrinking
or formal correctness certificate. These are 1,000 generated test cases, not
1,000 distinct program intents. Keep all old tests and report actual outcomes.
