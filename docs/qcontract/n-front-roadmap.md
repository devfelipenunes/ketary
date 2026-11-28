# N-front contract programming roadmap

Local QContract Alpha, scope: usability of existing mathematical
domains, not new algorithms, DSL, hardware targets or public publication.
Run independent fronts in parallel. Each round: specify evidence,
implement the smallest change, test positive/negative/unresolved cases,
inspect exact-head CI, compare artifacts, integrate only when approved,
then revisit the weakest remaining evidence. Do not mark work complete
based on a plan alone.

| Front | Deliverable | Acceptance |
|---|---|---|
| N1 Method | Contract-first workflow and intent selection | Executable examples; explicit state/operator scope |
| N2 Ergonomics | Reduce string/wire-index friction using existing masks | Same mathematical obligation, report, and budget for both forms |
| N3 Diagnostics | Read status, evidence and reserved work | Exact status retained; replay only supported domains |
| N4 Specification quality | Mutation and allowed variation controls | Analytically predicted status vectors, independent small reference |
| N5 Developer tasks | Small self-contained practice tasks | Runnable, independent expected outcomes, no hidden source imports |
| N6 Typed integration | IDE signatures and CI gating | Positive and negative mypy, all PASS gate, unresolved remains unresolved |
| N7 Reproducibility | Installed examples and structured artifacts | Exact commit, Linux/Windows/macOS, existing qualification |
| N8 External adoption | Held-out developer and agent task study | Independent participants, recorded protocol, no synthetic adoption claim |

## Baseline and current round

N1 and N4 have integrated examples (#535/#536). N7 has installed-wheel
documentation checks; each modification must requalify. N2/N3/N6 have a
candidate ergonomic API revision in a separate branch; do not document
as released until it passes and is merged. N5 introduces diagnostic
practice in this round. N8 remains an external gate (#165/#462).
#100 controlled performance, #35 release acceptance remain independent.
No public version tag, registry upload or new scientific novelty claim.

## Recursion and stop criteria

Use failed or surviving mutation controls to identify missing
requirements. A surviving circuit is not automatically defective.
Distinguish invalid input (exception), exact refutation, unsupported
scope and budget exhaustion. If an API convenience alters any existing
obligation ID or report, stop and fix the alias, not the engine.
If a learning exercise exposes a genuine usability issue, first improve
the explanation; add minimal API convenience only with typed parity
and regression evidence. Never weaken verification to improve pass rate.

Record objective results rather than a completion percentage:
number of runnable tasks, expected vs observed status vectors,
positive/negative controls, platform qualification and exact PR heads.
External studies and controlled performance remain unproved.
