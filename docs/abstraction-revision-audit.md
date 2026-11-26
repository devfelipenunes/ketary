# Abstraction revision audit — EXP15 / AUD10 / BENCH03

The target is one native Qiskit-backed API, not an alternate simulator or
DSL. Optimize existing primitives first; add higher-level intent only
where matched tasks demonstrate meaningful reuse or lower cognitive cost.

## Observations before this study

- #53 baseline: three shared runners, 30 observations per case, all 24
  cases matched native results. Native broadcast was ~6–7x faster than
  the staged single-wire batch at 40,000 instructions; generic apply_each
  was ~10x slower than native two-wire broadcast at 16,000 instructions.
- #57 replaced staging circuits with prevalidated native broadcast or
  aligned scalar calls, bound suffix rollback, and isolated symbolic/
  classical staging. 561 tests passed; the 10,000-instruction shared-run
  diagnostic was 33.49 ms instead of 179.39 ms across different runners.
- #58 added explicit pairs= on 12 two-wire fluent gates. On the same
  CI runner, 16,000 ordered pair instructions: prior generic apply_each
  155.84 ms, pairs= 30.48 ms (80.4% reduction); native-vs-pairs separately
  15.66/29.49 ms. Source study 331 vs prior 404 lexical tokens, native 254.
- #59 reused native parameter identity in symbolic apply/apply_each/repeat.
  A symbolic target stages native composition on a copy. Existing bound
  compose, execute and replay still require complete binding.

## Reproducible comparison

The dedicated workflow compares pre-PERF01 main ecc84a5 with the exact
candidate revision, each in its own environment with pinned dependency
versions. Both run 24 matched workloads (three randomized runner
replicates, 30 observations each); candidate adds direct pair grammar to
the same pair workload. Revision execution order is counterbalanced;
the raw artifacts retain timings, p95, oracle checks, RSS, commit,
environment, host and order. The comparison script reports per-runner
ratios, never pools heterogeneous host timings. Native speed variation
is a control. No hardware timing threshold or dedicated-host claim.

## Human/agent task protocol

Thirteen new authored held-out tasks cover ordered repeated pairs, nested
reusable layers, aligned angles, shared symbolic parameters, uncompute,
dynamic measurement order, grouped math, complex initial states, native variational energy, weighted MaxCut, phase oracles, multiple inputs and parameter rows.
The fixture prints prompts separately from trusted reference snippets.
The script executes only repository-authored solutions. It compares
complete strict complex operators, exact dynamic sequences, or selected
numeric outputs as appropriate. Negative control checks global-phase
difference is rejected. Record lexical Python tokens, calls and loops;
not LLM token counts or usability outcomes.

A separate future controlled study should randomize framework order,
provide equivalent documentation/context and time budgets, withhold
reference solutions and record correctness on unseen parameter values,
time, repair attempts, calls and actual model token counts. No external
LLM execution, human participants, independent study or performance
publication has been performed.

## Remaining architectural risks

- Native scalar/sequence gate methods are faster but validation and
  transaction overhead remains. Do not loosen rollback or validation to
  chase timings.
- Symbolic copy staging isolates parameter tables; inspect prefix scaling
  and name-collision rules before optimizing that path.
- Dynamic measure/reset copies the native prefix. Keep measurement ordering,
  classical operand mapping and late failure semantics; benchmark an
  alternative transaction separately rather than conflating with unitary
  append.
- Every added factory must preserve native allowlist, explicit execution,
  resource bounds, stable public stubs and export inventory.
- Ideal state memory remains exponential. Construction limits do not imply
  simulation, replay, tracing or full-operator verification support.
- Dedicated-host validation, real agent/human study, hardware/noise,
  generalized control-flow and public release remain separate and pending.

## High-level runtime diagnostics

Separate candidate-only matched workloads exercise native ansatz construction and binding, weighted Hamiltonians, phase oracles, independent input evolution, end-to-end sweep rows and selected probabilities. Each checks semantic equality before timing. The native comparison returns independent equivalent outputs; Ketary may include extra validation, snapshot or replay costs. No claims of quantum algorithm speedups or universal performance. Retain high-level.json in each revision artifact.
