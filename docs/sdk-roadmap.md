# Developer SDK roadmap (experimental)

No agents, MCP, new simulator, or DSL. Python 3.12 only; Qiskit authoritative.

| Stage | Delivered in proposed SDK PRs | Remaining |
|---|---|---|
| SDK01 | strict numeric expectation checks | broader edge and resource audit |
| SDK02 | direct gates, copy, atomic H batch | canonical syntax review; analyze compatibility alias |
| SDK03 | inspect/evidence/verify, immutable Contract and VerificationReport | report schema review |
| SDK04 | explicit basis, array or Result initial state | broader resource tests |
| SDK05 | 29 fixed logical gate types; central registry | MCX/variable-width gates and backend boundary |
| SDK06 | reduced density, purity, weighted Pauli expectation, Dirac, conditional probability, Schmidt, pure-state trace distance, Pauli variance, top-k | general mixed-state metrics and observable variance |
| SDK07 | incremental aligned comparison, selected checkpoint, historical budget retained | nontrivial alignment |
| SDK08 | native template binding, independent copy, compose | symbolic Circuit lifecycle RFC |
| SDK09 | Bernstein-Vazirani, QFT/inverse, small Grover and superdense | QPE, Simon and larger algorithms |
| SDK10 | text/math rendering and executed how-to examples | graphical extra, notebooks, dedicated machine benchmark |
| SDK11 | terminal sampling of selected wires | classical registers, measurement/collapse/reset/control flow RFC |
| SDK12 | existing package CI and release checklist | owner review, dependency/license re-review, controlled benchmark, release authorization |

## Contracts and scope

- Direct gate calls mutate and return the same Circuit; `.gates` remains compatible.
- `copy`, transforms and binding return independent circuits. `from_parameterized`
  binds a trusted native Qiskit template completely before validating it.
- `run(initial_state=...)` is explicit. Default is all-zero; basis labels
  use highest wire first. Result does not hold a reference to the builder.
- `inspect` never runs; `evidence` and `verify` reuse a snapshot. A selected
  property check is not a proof of the entire operator.
- Density output is dense and bounded; selected wires follow caller order.
  Weighted Pauli coefficients are real, finite and limited to 256 terms.
- `sample(wires=...)` samples ideal terminal marginal probabilities without
  collapse. It is not a measurement instruction or a classical-register result.
- QFT uses the positive Fourier exponent; `swaps=False` omits final
  bit reversal; inverse inverts the exact chosen circuit. Grover is a small
  reference implementation for 2/3-bit marked labels, not a general oracle.
- Superdense is coherent encode/decode, not a model of a distributed channel.
- No release is authorized; all current code remains experimental.

## Release checklist

- [ ] Required tests, upstream probes, strict consumer, build/install and audit green.
- [ ] Review exact API, docs, error contracts and supported gate/replay semantics.
- [ ] Run controlled benchmark on dedicated machine; record raw timings and RSS.
- [ ] Review dependency vulnerability/third-party license inventories and distribution obligations.
- [ ] Decide compatibility and changelog; explicitly approve publication separately.

Do not conflate terminal samples with mid-circuit measurement. Introduce a separate
classical execution-result contract via RFC before expanding that scope.

## Future classical execution RFC (SDK11)

Keep the existing Result as a pure-state snapshot. A distinct execution result for
classical registers must specify shots, register ordering, conditional control,
reset and collapse semantics, random seed and simulator capability. No conversion
from arbitrary classical outcomes into a pure Result. First validate terminal
measurements and register mapping against the chosen native backend; only then
consider dynamic circuits and mixed/noisy execution. Current marginal sampling
does not implement this model. Do not ship it without the RFC and oracle tests.
