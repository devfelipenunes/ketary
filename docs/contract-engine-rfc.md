# RFC — contract engine and native acceleration

Status: research proposal, not an approved runtime or packaging change.
Related #510 and #511. Preserve one public Python facade, Python 3.12,
Qiskit-authoritative circuit, existing Contract/Result behavior and limits.

## Architectural responsibilities

1. Python contract specification: immutable obligation, domain, quantifier,
   property, metric, tolerance, phase and method policy; snapshot vs operation
   vs channel vs statistical are distinct.
2. Analyzer: validate once, enforce scope and budgets before expensive calls,
   freeze one authoritative circuit export. Internal read-only packed
   instruction view is ephemeral, not another mutable IR.
3. Planner: pure capability/cost decision with deterministic explicit route,
   no silent guarantee weakening or optional-dependency fallback.
4. Backends: reuse NumPy/BLAS for dense linear algebra, Qiskit public Pauli
   and Clifford methods for symbolic invariants, existing optional QCEC for
   matching equivalence policies, statistical contracts for measured data.
   Add a private native kernel only after equivalent end-to-end advantage.
5. Composition: check domain compatibility, phases, error accumulation and
   contextual guarantees before deriving global obligations. Do not infer
   formal compositional proof from local numerical PASS.
6. Evidence: method/version, specification and input identity, exact scope,
   resource budget, residual, counterexample if available, reproducibility.
   No mutable-circuit cache, no hidden rerun, no implicit threads.

Native boundary: one batched call per obligation set, bounded packed buffer
or typed owned arrays, validate dtype/strides/length/overflow, no Python
callbacks during native loops. Release GIL only over owned/immutable data.
Native code has no authority to change circuit or verification semantics.
Errors/status distinguish invalid, unsupported, budget inconclusive, fail
and pass. For native wheel adoption propose Rust/PyO3 + maturin only after
ADR, measured benefit, license/SBOM and reproducible multi-platform wheels;
keep setuptools and public runtime unchanged during research. C++/pybind11
is a viable alternative. Use no fast-math where correctness is at risk.

## First experiment

Exact conjugation of one signed Hermitian Pauli by H,S,Sdg,X,Z,CX.
For up to 64 wires, two u64 masks and sign suffice; reverse gate traversal
computes U^dagger P U. O(g) word operations for this bounded representation,
O(g) packed input memory, not a general Clifford+T verifier. For one clean
ancilla and unitary U, U^dagger Z_a U=Z_a implies preservation of its zero
subspace; no implication of logical functionality. Non-equality requires
the property-specific witness/criterion before a full report can be issued.
Use independent dense Operator and Qiskit Pauli evolution oracles; compare
C++ and Rust C ABI, Python loop, public Qiskit with prebuilt Clifford and
full Ketary export. C ABI is a local research comparison, not PyO3 and not
production FFI. No public method or dependency added.

## Exit gates

E0 define semantics and report; E1 optimize existing admission/conversion
without changing guarantees; E2 benchmark native vs Qiskit and Python;
E3 specialize ancilla leakage including independent witnesses and tolerance
translation; E4 verify composition rules and adversarial cases; E5 integrate
internal engine only after review; E6 validate p50/p95, peak RSS, exact
head, compatibility, dedicated host #100, reproducible packaging and
external usability #165/#462. No timing assertions in shared CI. No
distribution or merge authorization inferred.

References: https://pyo3.rs/main/performance.html,
https://www.maturin.rs/project_layout.html,
https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.Pauli,
https://quantum-journal.org/papers/q-2026-07-23-2172/,
https://mqt.readthedocs.io/projects/qcec/en/stable/.

## Round 3 research increment

Prepared immutable ephemeral snapshot, gate classes validated once and wire indices mapped; no persistent cache or public API. Batch C++ bit-slicing up to 64 signed Paulis. Compare legacy export, preparation, scalar and batch, Qiskit Clifford prepared and full export with one tableau per batch. Exact sparse Clifford+T conjugation in Q(sqrt(2)), integer pairs over a shared power of two; no coefficient truncation. Caps: 64 wires, 100k gates, 32 T/Tdg, 4096 live terms and two million term visits; cap exhaustion is inconclusive, not failure or approximation. Numerical dense reference on small circuits. Leakage research: one arbitrary clean ancilla wire, 1–6 qubits, numeric unitary admission, SVD witness restricted to allowed inputs and direct reproduction, probability tolerance 1e-9 with diagnostic guard 1e-12; no certified roundoff. Generic effect residual squared agrees for exact unitary; timing routes differ in admission so no matched speedup claim. Includes analytic boundary case. No production changes or packaging.

## Round 4: integrated research engine

Immutable signed-Pauli transition obligations U^dagger post U=pre.
Explicit scope ignores circuit global phase. Preparation is validated at
the research boundary; identity hashes bind ordered admitted instructions
and width, not authentication or complete circuit semantics. Planner selects
Python, scalar/batch native, or sparse exact arithmetic with a declared
work cap. Auto uses an explicit native instance and an initial batch
threshold of eight, a heuristic derived from round 3, not a universal
optimum. Unsupported method and budget exhaustion are separate verdicts;
no weakening or hidden fallback. Sparse budget is shared conservatively
across the request; abort consumes remaining budget. Work counts propagation
visits, not witness generation or full process resources. Reports include
method, scope, identities, reason, and product-state witness on exact FAIL.
A nonzero Hermitian Pauli polynomial has a nonzero product-state
expectation: fix local Pauli axes supporting one nonzero monomial and
successively choose signs preserving a nonzero polynomial. The resulting
expectation is exact in the same integer ring, not a maximum-residual
witness. Dense independent replay validates small cases.

Composition checks two local identities with matching intermediate Pauli;
if both PASS, the combined identity follows by substitution. Otherwise
perform a separate direct check within a reserved portion of the budget;
local FAIL never implies global FAIL. Local reports accompany the derived
report; no persistent certificate cache or formal verification claim.
Three parallel correctness suites (mathematical, adversarial, native)
and a separate full-report performance/RSS job. Compare Qiskit Clifford
routes with identical report scope and witnesses. Linux high-water RSS
is whole subprocess including setup, not allocation peak; no guarantee.
Still no public API, runtime changes, new dependencies or merge.

## Round 5 — parallel research

Eight independent Linux jobs A–H on one exact head: joint clean ancilla
stabilizer subgroup and bounded numeric SVD; immutable Clifford sessions
with aggregate budget and 64-lane chunks; adversarial sparse exact-ring
tests; exact chains up to 100; bounded versioned evidence replay; stronger
Qiskit PauliList and Stim 1.15.0 comparison (research-only dependency);
externally sampled live RSS with ready/go/done handshake; four executable
algorithm examples. These are research modules, not new public APIs.
Session trust is internal and limited to frozen Prepared and immutable
tuples/bytes; no mutable-circuit cache. A joint ancilla space can be
preserved even when individual generators change (e.g. ancilla swap).
Exact zero leakage and numerical tolerance are separate specifications.
Evidence hashes do not authenticate. Re-evaluate against independent
input/spec, not merely a checksum. No assumption that composition is
faster; compare direct verification. No timing thresholds. Stim comparison
checks same transformed Paulis rather than sampling or entire circuits.
QFT/adder examples use research oracles, not new public contracts.

## Round 6 research

Separate exact zero-leakage from probabilistic tolerance in a typed subspace
planner, no downgrade. Research-only owned FFI buffer attached to an explicit
snapshot and batch session. Exact adjacent inverse cancellation before sparse
propagation, independent strict dense controls; cap applies after rewrite only
in this explicit experiment. Disjoint-wire tensor factorization can derive
positive local Pauli invariants even when global term expansion exceeds the
cap; local failure is inconclusive, not global failure. Version-bound evidence
with source fingerprints and strict JSON replay, not authentication. Stronger
Stim reference using text parser instead of per-gate append. Isolated live RSS
with identical fixture and no eager tableau, repeated requests and three trials.
All seven jobs independent, no new runtime dependency or public API.

## Round 7 — matched optimization experiments

Sparse: Clifford permutations are injective on unsigned Pauli labels, so
the accumulation dictionary can be replaced by direct assignment; commuting
T gates need not rescale all coefficients until canonical export. Preserve
exact Propagation output, term-work, cap and rejection semantics.
Session reports: group repeated post observables, share immutable identical
reports only within one request, retain original conservative work bound;
early terminate product-witness conditioning when polynomial is constant.
Compare unique and duplicate obligations separately, no global cache.
Composition: connected components of the CX interaction graph factor the
unitary into tensor products; each local Pauli image may equal plus or minus
its target, accumulate signs, produce global signed witness when opposite.
Non-Pauli local image or exhausted component budget remains INCONCLUSIVE.
No general arbitrary-gate equivalence. Three independent research CI jobs.

Additional independent jobs: restricted-column leakage computes the map on
every clean basis input (therefore also all coherent superpositions), not
only their individual probabilities. Uses native Statevector evolution for
columns, shared SVD and independently replayed witness. Compare with full
Operator for up to 8 wires; restricted research path admits up to 12 wires,
at most 4 data wires and 256 gates. 16*2^(n+k) bytes column payload vs
16*4^n dense operator payload, not actual peak RSS. No new public bounds.
Stage profiling measures preparation, admission, propagation, hashes,
example witness, warm report and cold full calls separately; medians are
not additive. Five independent research jobs.

Round 7 follow-up: component factoring's first dense control failed in CI.
Keep the original assertion and add explicit Qiskit dense vs Clifford
oracle, Pauli-label roundtrip and full sparse coefficient checks with
fixture/phase diagnostics. Do not adopt this route until explained.
Compact Clifford snapshot experiment validates packed bytes using bounded
NumPy arrays and a domain-separated version-2 binary identity. It is not
compatible with existing JSON circuit IDs. Compare semantic reports and
witnesses, not equality of IDs across schemas; no migration or public
change authorized. One bytes representation only, no mutable cache.

## Round 8: optimization roadmap experiments

Fix the round 7 dense residual expression: it omitted the right-hand U in
U^dagger P U - Q. Keep all oracle assertions and the independent target
comparison. Native sparse Rust uses bounded i128 integer coefficients
(32 T cap implies max coefficient <=4^32), insertion order and identical
work/term cap checks; C ABI is a research experiment, not a PyO3 decision.
Adaptive Pauli planner: exact inverse cancellation, backward conservative
support cone and optional factor route under a split work budget. Disjoint
gates commute with current Pauli support; no coefficient pruning. Report
identity refers to original circuit. Group duplicate Clifford obligations
only when reuse is substantial; threshold is heuristic. Scale to 100k
gates within existing research caps and compare explicit thread pools
without changing runtime threading. Channels use bounded numeric
CPTP adjoints and independently replayed forward witnesses; separate
from unitary contracts. Algorithm components and QCEC up-to-phase full
equivalence use distinct scopes. Dedicated host protocol remains
docs/release-validation.md / #100: shared CI is not controlled evidence.

## Round 9: compiled Python extension, isolated research distribution

Use a separate research Cargo crate and Maturin build. CPython 3.12 only;
PyO3 0.27.2 and Maturin 1.9.6 pinned as direct dependencies. Existing
setuptools distribution and public facade remain unchanged. No publication.
Compiled frozen PackedCircuit owns its bytes and validates bounds, native
calls detach the GIL only over Rust-owned data. No raw-pointer C interface
in the new adapter. Integer coefficient bound from round 8 extends to
witness conditioning by at most 4097 terms, still within i128. Native
transition returns a deterministic product-state witness rather than
transferring every sparse coefficient to Python. Python research adapter
validates exact input types and aggregate work budget, preserves semantic
report fields, assigns explicit binary v3 identity, and keeps optional
cone optimization separate. No public Contract or Result changes.
Cross-platform runner-local wheel builds and installed-wheel smoke;
Linux matched complete contracts with exact witness parity, dense
reference, budget parity, GHZ fixtures and explicit thread tests.
Cargo.lock generated and captured in artifact on first build; commit
reviewed lock before release, audit licenses/SBOM and reproducibility.
Wheel portability beyond runner OS is not claimed; no upload to registry.

## Round 10 — qualification gates

Exact joint clean subspace for Clifford+T: restrict U† Z_i U to the clean
input subspace. X/Y on an ancilla has zero compression, Z on that ancilla
is +1, and equality to identity for each generator is necessary and
sufficient for zero leakage of a unitary. Native exact propagation and
Python coefficient compression; reproduce failure witnesses in the clean
domain. No approximate fallback. Shared propagation budget, not a full
memory or witness bound. Algorithm corpus includes repetition encoding,
Toffoli compute/action/uncompute with distinct coherent action checks,
Grover snapshot and strict QFT numeric checks, with mutants. Match only
equal scopes when timing. Fresh Linux worker memory comparisons and
real SDK dense reference tests on installed Windows/macOS/Linux wheels.
Independent human study and controlled host remain separate gates; see
contract-engine-qualification.md. No production packaging or public API.
