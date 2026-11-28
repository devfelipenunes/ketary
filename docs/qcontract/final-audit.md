# R21 — methodology audit and claim boundaries

Audited integrated baseline 07a148baf2f1a778dbf8499fb7b4b8d28ff03a59.
PR #547 exact head f407173439345ab6b859ea4bdce9a204976785e1 passed
[three isolated-wheel jobs](https://github.com/devfelipenunes/ketary/actions/runs/46140369475)
and [six general SDK jobs](https://github.com/devfelipenunes/ketary/actions/runs/46140369429).
The preceding comparison against 6e7db049fa6b67ce67882c741b6308988b61452a
lists 18 changed files, all in docs/qcontract or the qualification workflow.
No engine or public API files changed in that comparison.

| Finding | Correction or boundary |
|---|---|
| Plan described as independent obligations | Conjunction does not imply mathematical independence; diagnostics may be redundant |
| Budget described only as a logical cap | Explain equal per-item floor allocation and zero quota; splitting changes resource policy |
| Snapshot assumed for every predicate | Correctable is circuit-independent and reports empty snapshot tuple |
| Evidence inventory checks keys | Inventory is not independent validation or authenticated provenance |
| Examples and guides repeat navigation | Single start page, advanced guides remain available |
| Comparative claim lacks matched current QContract fixtures | R24 supplies authored same-property Qiskit comparison; no usability or speed claim |
| Main push workflow enabled | Post-merge execution must be observed; PR success is not main run evidence |

The exact-head results above are observed, not independent peer review.
The available workflow lookup only returns PR-triggered runs; main-push
qualification cannot be verified using that lookup. Do not report it as
passed. The final candidate will rerun the integrated documentation and
all previously registered exercises on the same installed wheels.

## Outstanding gates

- #35: release/name/notice review and explicit publication approval.
- #100: controlled dedicated-host performance and memory profiling.
- #165: independent held-out developer/agent evaluation.
- #462: independent approval of the participant task packet.

All four were checked open. No closure, publication, recruitment or
controlled-host activity is implied by this audit.
