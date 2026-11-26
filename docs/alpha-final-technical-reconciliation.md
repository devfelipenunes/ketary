# Final technical reconciliation candidate

Refs #91 #110 #56 #345 #258. Baseline 963e7643744d6912256ab1f054736a3ec8871e99.
No new public API or release. #460/#501 explicitly paused. Other excluded
gates #35 #100 #165 #462 remain open. This does not reclassify historical
closed duplicates as completed implementations.

- #91: `alpha-final-technical-ledger.json` lists every one of the 39
  explicit capped stub methods, implementation owner, scope and existing
  test files. Fixed and legacy path families remain separate; caller
  payload, native scratch and RSS are not equivalent. Table read model now
  validates all provided labels before evaluating any row, preserving
  existing cap/order/duplicates/empty output and error type. Existing
  budgets and valid inputs unchanged.
- #56/#345: 52 historical expressivity rows (51 plus epic #345) preserve
  qualified, consolidated, not planned, historical closed and open
  dispositions. 13 rewrite fixtures, 100 LANG cases, 27 parameter rows,
  paired longitudinal diagnostics and 37 original bounded functional
  alternatives already qualified. Cross-family #163 teleportation
  matched source/cost and independent held-out writing remain explicit
  gaps; no claim of all 51 implemented or of independent study.
- #110: exact QCEC optional inventory previously found no installed
  notice hashes for ANTLR4 4.13.2 and nanobind-backend 1.0.0. The new
  narrow workflow downloads only the two hash-pinned public wheels
  and inspects ZIP membership and metadata without installation or
  execution. Missing members remain negative evidence. Sources:
  https://pypi.org/project/antlr4-python3-runtime/4.13.2/
  https://github.com/antlr/antlr4/blob/4.13.2/LICENSE.txt
  https://pypi.org/project/nanobind-backend/1.0.0/
  https://github.com/wjakob/nanobind
  ANTLR tagged license is BSD-3-Clause; nanobind-backend PyPI
  classifier says BSD and parent project is BSD-3-Clause. Parent
  license is not exact binary provenance or legal clearance. Neither
  optional dependency is bundled in Ketary's wheel. No external
  package content is committed. Stock sdist remains distinct from the
  experimental deterministic archive procedure.
- #258: preserve historical evidence snapshots; current main #502
  exact-head CI complete, integrated tree verified, new push validation
  pending at authoring. Final acceptance requires actual integrated
  evidence, scope decisions and open-gate review.

All additions require full exact-head and post-merge validation.
