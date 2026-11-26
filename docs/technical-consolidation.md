# Technical consolidation — baseline 2026-11-26

Starting integrated revision: 8e51a022b532dd0ed563e2009c4bb5f80dbf233f
(PR #87, preceded by #79, #81, #83 and #85). Python 3.12, Qiskit
2.6.2, experimental 0.1.0.dev0. This is not a release or a promise
of hardware support. Qiskit is still the authoritative circuit and
default execution path; the native bridges are research-only.

## Verified evidence and outstanding questions

| Work | Exact candidate CI | Status |
|---|---|---|
| #79 BENCH04 | 45764869707, 45764869826 | 15 jobs passed; integrated |
| #81 BENCH05 | 45765241303, 45765241266 | 15 jobs passed; integrated |
| #83 prepared/fusion | 45765639002, 45765639015, 45765638853 | 10 jobs passed; integrated |
| #85 translation ablation | 45766023430, 45766023461 | 15 jobs passed; integrated |
| #87 extended coverage | 45766497621, 45766497643, 45766497577, 45766497645 | 11 jobs passed; integrated |

GitHub Actions run URLs: https://github.com/devfelipenunes/ketary/actions/runs/
followed by the listed ID. These are candidate checks, not proof that every
combined post-merge workflow has run. #87 SDK tests: 678 passed, 1 skipped,
93% branch-inclusive coverage (test job log); dynamic suite separate.

- BENCH07: 282/282 supported case/input/runner comparisons favored direct
  execution over Qiskit Statevector median; only 47/108 original cases
  directly supported. No universal speed claim.
- #83: prepared batch of 16 rows ~1.136x median speedup against repeated
  calls; synthetic fusion ~3.8x, mixed workloads not consistently improved.
- #87: direct CP/RZZ/CCX/MCX prepared execution beats decomposed variants
  in authored workloads. MCX packing is Python-only; owned-output copy
  removal has no consistent timing benefit. No reason to prioritize
  copy removal absent new evidence.
- Portable vs native flags are not SIMD proof; CPU/local MPI were exercised
  in CI, GPU/cuQuantum/multi-node and dedicated-host evidence unavailable.
- Existing SDK surface inventory: 94 core and 169 advanced entries.
  Review usage before expanding. Historical authored token study had
  Qiskit 254 vs Ketary 404 tokens; retain negative evidence.
- Previous architecture audit showed a 13-module SCC including local
  imports, not an eager import cycle. Recompute, do not assume unchanged.
- Resource estimates are payload bounds, not process RSS. External
  verification, statistical checks, state checks and operator checks have
  different scopes. No formal verification claim.
- Dedicated-host benchmark, independent human/agent evaluation, legal
  redistribution review, and owner release approval remain outstanding.

## Ordered backlog

| ID | Issue | Priority | Scope |
|---|---|---|---|
| TC01 | #88 | P0 | Baseline/evidence registry |
| TC02 | #89 | P0 | Native ABI/boundary qualification |
| TC03 | #90 | P0 | Mathematical differential corpus |
| TC04 | #91 | P0 | Resource/preflight audit |
| TC05 | #92 | P0 | Ownership/numerical invariants |
| TC06 | #93 | P0 | Replay/report robustness |
| TC07 | #94 | P0 | Verification semantics/mutation |
| TC08 | #95 | P0 | CI reproducibility |
| TC09 | #96 | P1 | Direct gate coverage |
| TC10 | #97 | P1 | Prepared parameter semantics |
| TC11 | #98 | P1 | Batch/fusion ablations |
| TC12 | #99 | P1 | End-to-end benchmark refresh |
| TC13 | #100 | P1 | Dedicated CPU/RSS |
| TC14 | #101 | P1 | ISA/cache/threading |
| TC15 | #102 | P2 | GPU/cuQuantum/multi-node |
| TC16 | #103 | P1 | Backend promotion RFC |
| TC17 | #104 | P1 | Coupling/ownership |
| TC18 | #105 | P1 | API and typing |
| TC19 | #106 | P1 | Expressivity and negative evidence |
| TC20 | #107 | P1 | Executable documentation |
| TC21 | #108 | P1 | Dynamic/statistical correctness |
| TC22 | #109 | P1 | Verification scaling |
| TC23 | #110 | P1 | Packaging/licenses |
| TC24 | #111 | P1 | Release candidate gate |
| TC25 | #112 | P2 | Developer pilot readiness |
| TC26 | #113 | P2 | Agent evaluation readiness |
| TC27 | #114 | P1 | Legacy issue reconciliation |
| TC28 | #115 | P1 | Regression and decisions |

## Execution and dependencies

Wave A: TC01, TC03, TC05, TC06, TC08. TC02 and TC04 in parallel,
then TC07. TC01/03/05/06 begin with seeded all-gate tests in this PR,
not complete qualification. TC27 reconciles prior issue scopes without
closing unresolved hardware/release/independent evidence.

Wave B: TC09/10 after TC02; TC11/12 after TC03/09/10. TC13/14 after
TC12; TC15 needs an authorized equipped machine. TC16 is a decision,
not implementation permission. Reject promotion if semantic coverage,
ABI, resources, licensing or performance do not justify it.

Wave C: TC17/18/19/20/21/22; no gratuitous API additions or second IR.
TC23/24 after P0 gates and dedicated CPU evidence; TC25/26 prepare
external protocols, but actual participation and model experiments
need separate evidence. TC28 spans every wave.

## Definition of done

One coherent PR per issue or explicitly grouped slice. Exact commit,
native/analytic oracles, negative cases, documented scope and limits,
raw benchmark evidence where applicable, full relevant CI and review,
merge commit, integration/post-merge verification. Record failed
hypotheses and unsupported cases. Timing tests are diagnostic, not
noisy CI thresholds. No claim of independent review from self-review.

Autonomous decisions permitted within existing compatibility and research
scope: private refactors, regression tests, matched experiments, CI fixes,
documentation and issue maintenance. Breaking API, new default engine,
new platform guarantees, publication/tagging, external research
participation and deployment require separate acceptance. See AGENTS.md,
release-validation.md and compatibility.md.
