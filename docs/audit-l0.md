# L0 engineering review

Baseline: main at 791ffa39634f7a0c54c3b249f2ec9aff5c9a909b, CI run 45736946909:
201 tests, wheel/sdist installed, dependency audit and benchmark passed.
This is a source audit and experimental evidence, not a certification.

| Area | Finding | Disposition |
|---|---|---|
| Mathematical accuracy | Near-normalized accepted states biased fidelity | Normalize overlap by both squared norms; regression |
| Native interop | Replay and optimization use gate names; renamed native gates need rejection | Check canonical name; regression |
| Memory | Full probability dictionaries can dwarf the state payload | Bound materialized outcomes; SVD and whole-process allocation remain open |
| Documentation | Architecture table outdated; no complete user-oriented guide | Diataxis-style docs and executed snippets |
| Quality | Test count not coverage | Branch coverage report and raw JSON; no arbitrary threshold until measured |
| Benchmark | Only build/run and one RSS scenario | Add compose, export copy and trace; expand workloads and controlled hardware later |
| Optimization | Native transpile not exposed, restricted inverse cancellation only | Document supported boundary; evaluate explicit Qiskit transpile with layout/phase contracts before expanding |
| Typing | Public signatures incompletely annotated | Follow-up typed API and static checks; no second interface |
| Distribution | Versions partially floating; audit is a snapshot | Reproducible constraints, CI provenance, third-party notices and review before release |
| Usability | Automated journeys only | Human comparison with Qiskit tasks remains pending |
| Release | No publication authorized; name availability and license obligations not verified | Owner gate and manual review before publication |

L0 status: core, result, algorithms, checks, diagnostics and replay are
implemented for the strict supported subset. Not every original aspirational
requirement is complete. The distinction between an experimentally verified
feature and an approved public release remains explicit.
