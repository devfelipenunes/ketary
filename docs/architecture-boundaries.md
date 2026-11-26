# Module boundaries and architectural debt

Baseline: CORE01–CORE10 and #42; updated for private execution consolidation.
Static audit of all Python modules under src/ketary. This is an import and
responsibility audit, not a performance or concurrency proof.

## Ownership map

| Group | Modules | Responsibility |
|---|---|---|
| Public facade | __init__, __init__.pyi, py.typed | exports and type contract |
| Construction | _circuit, _algorithms, _ergonomics | native circuit builder, factories, ordered selection, binding/sweep |
| Math and predicates | _result, _observable, _contracts, _statistical | snapshots, real Pauli sums, numerical/statistical predicates |
| Verification | _checks, _trace, _verification | operators, explicit traces, comparison and evidence |
| Native integration | _adapter, _execution, _classical, _external, _transpilation | validation, optional dynamic/external execution, logical transpile |
| Logical artifacts | _replay, _inspection, _plan | strict replay, bounded read models, explicit query plan |
| Transformation | _optimization, _gate_specs | conservative cancellation, allowlisted gate metadata |
| Presentation | _reports, _resources, _visualization | verdict/export, logical resource accounting, text/SVG |
| Shared foundation | _validation | scalar validation and resource guards |

This classification assigns responsibilities; modules can contain multiple
concerns. All 25 Python modules including the facade are accounted for.
The stub and typing marker are not runtime Python modules.

## Actual direct imports (including local imports)

| Dependency | Direct source modules |
|---|---|
| qiskit | _adapter, _checks, _circuit, _classical, _observable, _replay, _result, _transpilation, _verification |
| numpy | _checks, _execution, _result, _trace, _validation, _verification |
| qiskit_aer | _classical only |
| mqt | _external only |

_trace uses Statevector indirectly through _adapter._sdk. _optimization
uses native validation and native objects without a direct Qiskit import.
This table does not mean the remaining modules are transitively backend-free.
Observable can be constructed without importing Qiskit, but native conversion
uses SparsePauliOp. Contract depends on Result, which owns NumPy data.

## Coupling and risks

| Observation | Risk | Recommendation |
|---|---|---|
| _circuit holds builder, native imports, transformations and orchestration | growth of a central facade | keep public facade; extract private responsibilities only when change pressure justifies it |
| _result contains snapshot, sampling, math and checks | costly changes touch unrelated concerns | measure churn; separate private numerical helpers if needed |
| _circuit invokes _checks and _trace, which locally import Circuit | runtime back-references | document; avoid new top-level import cycles |
| _result and _contracts reference each other (local in Result) | tight predicate/snapshot coupling | preserve shared evaluation, avoid another verification implementation |
| _verification uses _replay helpers and Circuit; _reports lazily accesses Evidence | schema and diagnostic coupling | keep artifact validation centralized, version explicitly |
| Optional native integrations isolated in two modules | accidental dependency expansion | guard direct imports and core-only execution in CI |
| Native Qiskit imports spread among nine modules | broad impact of Qiskit changes | maintain tested dependency contract; consolidate only specific duplicated integration logic |

Local imports postpone initialization, not dependency inversion. A protocol
or abstract class alone does not remove native assumptions. The architecture
is appropriate for a Qiskit-backed SDK and not ready to claim arbitrary
backend substitution.

## Guardrails (implemented by tests)

- The direct native/optional import inventory is checked using Python AST,
  including imports within functions. It does not detect dynamic imports
  assembled at runtime or transitive dependency changes.
- A core-only subprocess blocks Aer and MQT imports, constructs an Observable
  and verifies a Bell snapshot. This checks optional dependency isolation
  along that workflow, not every execution path.
- Eager internal import graph must be acyclic; _validation and _gate_specs
  cannot eagerly import internal modules. Function-local imports are excluded
  from this cycle check, not claimed to be acyclic.
- Existing signature, compatibility, native-oracle and packaging tests remain
  required. No new runtime dependencies.

## Evolution proposal (not implemented)

A01 — maintain the module map, diagrams and decision records with changes.
A02 — audit native integration duplication; isolate specific functions if
a second consumer or concrete defect justifies extraction.
A03 — review local dependency cycles and introduce narrow internal protocols
only where they simplify real tests/changes. No general backend abstraction.
A04 — consider splitting _circuit/_result internal helpers when changes
become difficult; keep public signatures, types and ownership unchanged.
A05 — verify cost and phase/order semantics against the existing suite after
any refactor; compare equivalent workloads. No architectural rewrite merely
to resemble a hexagon.

A01 is implemented. A02 is partially addressed by extracting ideal execution
and reusing the trace cursor; A03 adds eager-import cycle and foundation guards.
A04 remains conditional; A05 uses the existing validation and benchmark protocol.
See [architecture progression](architecture-roadmap.md) for exit criteria. Independent human validation and dedicated-host performance remain
separate acceptance tasks.
