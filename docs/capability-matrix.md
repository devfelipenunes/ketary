# Capability and qualification matrix

Current bounded experimental routes, not a general Qiskit replacement.
Baseline: integrated #374, tree-equivalent validated head 9d51aa9d.
For exact limits and ownership see [resource contracts](resource-contracts.md).
For remaining gates see [production fronts](production-fronts.md).

| Route | Supported domain | Boundary |
| --- | --- | --- |
| Circuit/run | Bound ideal statevector; native standard logical gates | 64 MiB default state payload, 22 wires at that budget; not RSS or hardware |
| from_qiskit | Strict bound native logical import | No silent metadata/barrier/layout loss |
| from_symbolic / bind_partial | Native parameter identity; explicit later binding | <=62 wires, 10000 gates, 4096 parameters; no symbolic replay |
| from_synthesized / control / from_unitary / prepare_state / evolve_exact | Trusted bounded native gate-only inputs; strict complete operator verification | <=5 total wires, <=256 synthesis input instructions, <=10000 output instructions; 1e-9 component residual; preparation promise only on zero input |
| evolve | Commuting real Pauli terms, bound or supported symbolic time | <=8 wires, <=256 terms, <=10000 estimated gates; reject noncommutation |
| evolve_product | Ordered Lie/Strang approximation | <=8 wires, <=64 steps, <=10000 estimated gates; explicit approximation |
| expectation_jacobian | Qualified parameter occurrence shifts | <=8 wires, 32 parameters, 128 shifted circuits, 8 observables |
| expectation_hessian | Qualified second derivatives | <=8 wires, 8 parameters, 8 occurrences, 256 shifted circuits |
| quantum_geometric_tensor | Projected ideal pure-state derivatives | <=8 wires, 16 parameters, 32 occurrences, 64 shifts plus base |
| from_dynamic / run_shots | Optional Aer; native bit/register equality, nested gate-only branches | <=12 wires/bits, <=1024 nodes including both branches, depth 3, <=10000 shots; no loops or conditional measurement/reset |
| run_density / run_noisy | Local native density matrix; noise optional Aer | <=8 wires, <=1024 instructions; no arbitrary noisy measurements |
| run_channel | Standard final native Kraus CPTP map | <=4 selected wires on <=8-wire circuit; <=16 matrices; no mid-circuit execution |
| expectation_complex / Observable.product / commutator | Native complex Pauli bridge | <=256 input terms for expectation; bounded 4096 term pairs for algebra; Observable remains real |
| project_annotated | Separate ideal projection and native snapshot | <=22 wires/10000 instructions; bounded JSON metadata; no layout/classical data or scheduling claim |
| compare / metrics / external_equivalence | Selected-input, dense operator and optional QCEC checks | 12 wires/256 gates, dense 8 wires, QCEC 22 wires/256 gates respectively; distinct scopes |
| Evidence.minimize | Fixed witness greedy deletion, reference evaluated once | <=128 attempts; local single-deletion minimum only after complete unchanged pass |
| transpile_for | Local native target handoff | <=12 logical wires/1024 instructions; no device execution |
| Platform | Python 3.12; Qiskit 2.6.2; optional Aer 0.18.4 | Earlier three-OS qualification, latest Linux CI; no other Python support or general hardware portability |

## Qualification is distinct from capability

All entries describe implemented bounded routes, not guarantees for all
possible inputs. No automatic backend choice, release, publication, device
execution or formal verification. Core/Advanced/Native/Compatibility are
learning categories, not release-stability levels. See
[mathematical contract matrix](mathematical-contract-matrix.md).
