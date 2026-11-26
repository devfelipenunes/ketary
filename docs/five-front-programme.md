# Five-front engineering programme

Baseline 7dbbd3fe. This is a coordination map over existing issues, not a
new runtime architecture. Avoid duplicate broad tickets; use linked issues
and bounded acceptance. No release or version bump.

| Front | Coordinator | Existing work | First distinct deliverable |
|---|---|---|---|
| Architecture | #253 | #240 #190 #105 #204 #210 | #259 ownership inventory |
| Mathematics | #254 | #243 #247 #248 #175 #182–184 #188–189 #225 | #260 local observable workflow evidence |
| Workflows | #255 | #242 #214–224 #226 #197 #165 #211 | #261 direct/preexpanded native QAOA comparator |
| Performance | #256 | #244–247 #193 #171 #227 #228 #98–102 | #262 QueryPlan stage attribution |
| Verification | #257 | #249 #118–125 #133–137 #224 #241 | #263 nonfinite native expectation |
| Integration | #258 | #198 #230 #250 | #264 combined exact-head candidate |

## Sequence
1. Fix demonstrated correctness defects first. Keep prior valid behavior.
2. Establish matched stage-level measurements and independent oracles.
3. Compare research abstractions across distinct workflows before approval;
   retain losing examples and distinguish unsupported behavior from defects.
4. Integrate exact-head green PRs, inspect merged trees, then verify combined
   candidate. No adding test counts from separate branches.
5. Reconcile issue acceptance against concrete evidence. Independent pilots,
   source-pinned external corpus, dedicated-host RSS and legal review remain
   separate gates.

Public design remains one Python SDK and one native authoritative circuit.
No generic backend, automatic approximation, hidden execution or new DSL.
Shared CI timing is diagnostic. Tests are authored by the same development
process, not independent evaluation. Preserve compatibility, global phase,
ordered wires, resource limits and optional dependency boundaries.
