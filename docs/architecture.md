# Experimental modular architecture

QuantumCircuit is the authoritative mutable program. Result owns an independent
ideal-state snapshot. No parallel mutable IR, second simulator or backend.

| Module | Responsibility |
|---|---|
| _validation | integer/angle/tolerance validation and payload guards |
| _adapter | strict native gate and circuit validation; lazy Qiskit import |
| _circuit | facade, mutation, transformations, explicit execution |
| _result | defensive snapshot, sampling, math and state checks |
| _checks | residuals and bounded complete operator checks |
| _trace | explicit state evolution and aligned checkpoint diagnosis |
| _resources | logical resource reports and text drawing |
| _algorithms | Bell, GHZ and explicit Deutsch-Jozsa oracle factories |
| _optimization | exact adjacent inverse cancellation |
| _replay | bounded logical JSON artifacts |

The public package has a src layout; private modules are not a second API.
Transforms and public import/export isolate objects. JSON is not a persistent
mutable circuit model. Explicit calls may allocate temporary memory. Python
3.12.x only. Review current scope in [reference](reference.md) and
[audit](audit-l0.md). Release and human evaluation remain pending.
