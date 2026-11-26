# Developer SDK roadmap (experimental)

No agents, MCP, new simulator, or DSL. Python 3.12 only; Qiskit authoritative.

| Stage | Delivered in proposed SDK PRs | Remaining |
|---|---|---|
| SDK01 | strict numeric expectation checks | broader edge and resource audit |
| SDK02 | direct gates, copy, atomic H batch | canonical syntax review; analyze compatibility alias |
| SDK03 | inspect/evidence/verify, immutable Contract and VerificationReport | report schema review |
| SDK04 | explicit basis, array or Result initial state | broader resource tests |
| SDK05 | 29 fixed gate types plus bounded MCX; central registry | broader multi-control synthesis and backend boundary |
| SDK06 | reduced density, purity, weighted Pauli expectation, Dirac, conditional probability, Schmidt, pure-state trace distance, Pauli variance, top-k | general mixed-state metrics and observable variance |
| SDK07 | incremental aligned comparison, selected checkpoint, historical budget retained | nontrivial alignment |
| SDK08 | native binding, explicit symbolic Circuit and full binding, copy, compose | partial binding and symbolic transforms deliberately excluded |
| SDK09 | Bernstein-Vazirani, QFT/inverse, small Grover, superdense, phase-gate QPE and Simon oracle iteration | generic QPE, Simon GF(2) solver and larger algorithms |
| SDK10 | SVG histogram, Bloch coordinates, executed how-to/notebook, paired density and Pauli query benchmarks | full graphical circuit/Bloch sphere and dedicated machine benchmark |
| SDK11 | terminal marginal sampling; explicit one-register dynamic Circuit, measure/reset, conditional X/Z, native shot results and teleportation | multi-register and general control flow deliberately excluded |
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

Do not conflate terminal samples with mid-circuit measurement. The explicit dynamic mode below returns a separate ShotResult.

## Classical execution RFC (SDK11)

Keep the existing Result as a pure-state snapshot. A distinct execution result for
classical registers must specify shots, register ordering, conditional control,
reset and collapse semantics, random seed and simulator capability. No conversion
from arbitrary classical outcomes into a pure Result. First validate terminal
measurements and register mapping against the chosen native backend; only then
consider dynamic circuits and mixed/noisy execution. Current marginal sampling
does not implement this model. The experimental implementation below is validated separately from the pure-state core; review is required before release.

## Developer visualization

`result.visualize.histogram(k=8)` returns bounded SVG text (no new dependency).
`result.visualize.bloch(wire=0)` returns the three Bloch coordinates, not a
sphere image. The notebook `examples/quantum_engineering.ipynb` demonstrates
construction, contracts, mathematical queries, diagnosis and search; its cells
are exercised by pytest. Query benchmarks compare equal outputs separately
from construction and execution. Existing process RSS measurements remain
statevector scenarios, not a bound on every query.

MCX supports 1–7 closed controls (CX/CCX canonical for 1/2), distinct wires; replay accepts bounded variable width. `phase_estimation(phase, precision)` estimates a known phase-gate eigenvalue on |1>, not arbitrary unitary. `simon(secret)` constructs one iteration with a known two-to-one oracle, yielding orthogonal samples; classical recovery remains external.

### Symbolic lifecycle

`Circuit.symbolic(n)` opts in to native Qiskit `ParameterExpression` angles. `Circuit.parameter(name)` creates a native parameter. `bind({parameter: real_value})` covers exactly the free parameters and returns an independent normal Circuit. Default builders reject symbolic angles; unbound execution, replay, inspect, optimization, operator checks and trace fail explicitly. No second IR; no implicit binding or partial binding.

### Dynamic execution candidate

Install the optional `ketary[dynamic]` extra (Qiskit Aer 0.18.4), leaving
core dependencies unchanged. `Circuit.classical(n, num_clbits)` owns a native
QuantumCircuit with one classical register; gates, measure, reset and bit-conditioned
X/Z mutate. `run_shots(shots=...,seed=...)` uses native Aer, no second simulator.
ShotResult contains immutable sorted counts and empirical frequencies; labels
are highest classical bit first. No pure-state conversion or replay/transform
of dynamic circuits. Bound 12 wires/bits, 1024 top-level operations and 10000 shots;
payload budget is not a total process RSS bound. No hardware, arbitrary control
flow, noisy execution, classical expressions or external dynamic imports.
Teleportation prepares RZ(phi)RY(theta)|0>, measures both Bell wires, applies
actual feedforward, measures output; verify=True first reverses preparation on
output. CI tests multiple phases and amplitudes, reset and seeded counts.
The optional dependency has its own inventory and vulnerability scan; passing
metadata inventory is not license approval. See IBM Qiskit dynamic circuit docs
(https://quantum.cloud.ibm.com/docs/en/qiskit/classical-feedforward-and-control-flow).
