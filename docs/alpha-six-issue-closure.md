# Six existing alpha issues: bounded closure candidate

Refs #151 #152 #153 #157 #293 #298. No installed API change. Fill matched
source/timing gaps rather than promote new abstractions.

- #151: strict prepared-state reflection sign I-2|v><v|, uniform amplification
  2|s><s|-I and marked probability separately. Existing generalized research
  positive reflection remains distinct; compare phase explicitly.
- #152: basis, product and dense unitary preparation. Native extension is
  implementation-specific; independently validate zero column and unitarity.
- #153: parity XOR offset, explicit truth-table composition and marked-label
  phase oracle; all columns including occupied target, complex input, inverse.
- #157: direct measured X/Z conditions, reset and nested native gate-only
  conditions. Deterministic and sampled truth-table distributions, same
  local Aer shots/seeds. Nested import cost included, logical counts.
- #293: four paired optimization objectives (spin, excited penalty, overlap,
  multi-observable); H2 separately qualified. Same optimizer, histories,
  independent formulas/eigenvalues.
- #298: two planted defect/repair applications with selected and full checks
  and reproduced witness. Typed evidence JSON and QPY circuit pair differ.

Preserve raw timings and negative results. Source metrics count authored
builders and relevant helpers, excluding installed library internals and
common oracle code. Strict common-basis operators, not dynamic unitary
claims. Shared CI is diagnostic. No timing threshold or weakened test,
no public API or release. Close only after exact-head CI, artifact review
and post-merge CI.
