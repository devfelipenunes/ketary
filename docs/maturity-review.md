# Maturity review and release-readiness gates

Scope: internal pre-alpha; no version bump, tag, upload or release.
The owner authorized engineering refinements, not distribution.

## Evidence at the challenge baseline

- #212: six SDK jobs passed; API lifecycle inventory covers 307
  declarations, including 34 compatibility entries. No removal.
- #213: nine jobs passed; 27 parameter workload instances, all five
  paths matched tested output. Native Qiskit binding remained faster.
- #231: seven jobs passed; 100 named challenge instances plus manifest
  check, 101 passed with Aer (85 non-measured and 15 measured cases).
  SDK candidate: 1164 passed, 27 skipped, 25 warnings, 95% branch-inclusive.
  Main after #231: 6e499af1e4f5c5e52af42c2065356547028c09f5.
- #232: symbolic exact evolution candidate; first iteration found
  native expression overflow leaking ZeroDivisionError and two invalid
  checkpoint fixtures. Preserve checkpoint scope and normalize the
  binding error; second iteration must pass every required workflow.
- #233: mixed Pauli Y synthesis candidate; prior 92 common-basis gates
  across 12 evolution cases reduced to 88 in candidate diagnostics
  (native 72). Strict phase residual <=9.23e-16. No universal speed claim.
- #234: remove sweep row transpose/reparse; benchmark old-path emulation
  versus direct preparation. Pending CI at time of writing.

## Gap ledger and review decisions

| Workflow | Evidence | Decision / next gate |
|---|---|---|
| Fundamental / graph / GHZ | Exact prepared-state or operator fixtures | Retain fluent gates, topology helpers and named state factories |
| Fourier / BV / Grover / QPE | Analytic fixtures | Retain existing named factories; generic controlled block is not required for this scope |
| Parameterized ansatz | Native identity and ordered binding; independent row sweep | Preserve bind and sweep semantics; profile native binding before further optimization |
| Hamiltonian construction | Commuting exact evolution; explicit rejection | Keep evolve, reject silent product formula; qualify symbolic scope separately |
| Parity/constant oracle | Complete small truth tables, including occupied targets | Keep explicit oracle promise; general Boolean synthesis remains research |
| Error syndromes | Ten deterministic ideal bit/phase syndrome instances | No generic QEC or fault-tolerance claim; add logical superposition and noise study separately |
| Dynamic | Five ideal measured cases | Existing restricted Aer mode; no hardware execution |
| Composition | Ordered remap, repeat, inverse, immutable compose | Existing APIs remain canonical; no separate layer/sequence DSL |
| Verification | Deliberate PASS/FAIL/INCONCLUSIVE and evidence | Numerical verdict scope remains explicit; no formal proof claim |
| Usability | Authored snippets only | Independent human and agent study not done (#165/#211) |

The 100 challenge instances are not 100 distinct algorithms and do not
replace external, source-pinned benchmark circuits or held-out trials.
A challenge that passes is not proof of all valid inputs. Coverage and
test counts are diagnostic, not target-driven promotion criteria.

## Release gate checklist

| Gate | Status at baseline |
|---|---|
| Exact candidate SDK checks / typing / install smoke | Passed for #231 |
| Integrated main tree | Identical to #231 tested candidate |
| Post-merge CI | Not established by PR-triggered evidence; obtain push workflow evidence |
| API/stub inventory and compatibility | Checked, continue reviewing changes |
| Runtime/dynamic/build license and vulnerability artifacts | Produced by CI, legal redistribution review still required |
| Warning review | SciPy sparse efficiency in benchmark and intentional nonfinite Pauli negative fixture; inspect all new warnings |
| Controlled dedicated host / peak RSS | Outstanding; shared CI insufficient |
| Independent developers/agents | Outstanding |
| External source-pinned benchmark instances | Outstanding |
| Version, name availability, owner release decision | Outstanding; no publication |

Use the existing [dedicated host protocol](release-validation.md) and
[API decision policy](api-decision-policy.md). Verify exact-head checks for
every PR and the combined main state; never sum tests on divergent branches.
