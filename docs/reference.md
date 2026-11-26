# API reference (experimental L0)

The public import is `import ketary as q`. Circuit factories return Circuit; recover_simon returns a classical label or None.

| Surface | Methods and behavior |
|---|---|
| Factories | Circuit(n), bell(), ghz(n), constant_oracle, parity_oracle, deutsch_jozsa, bernstein_vazirani, qft, grover, superdense, phase_estimation, simon, teleportation, from_qiskit(qc). recover_simon is a classical helper. |
| Circuit / Circuit.gates | h,x,y,z,s,sdg,t,tdg,sx,sxdg(q); rx,ry,rz,p(theta,q); u(theta,phi,lam,q); cx,cy,cz,ch,swap(a,b); cp,crx,cry,crz,rxx,ryy,rzz(theta,a,b); ccx,cswap(a,b,c); mcx(controls,target). Mutate and return Circuit. Direct h_many(wires) also mutates. |
| Circuit | num_qubits, append(gate,wires) mutates; compose(other,wires=None), inverse(), decompose(reps=1), optimize(), transpile(basis_gates,seed=42), to_qiskit(), to_json(), Circuit.from_json(payload) do not mutate source. Decompose only lowers SWAP. |
| Execution | run(mode="statevector",max_bytes=64 MiB,initial_state=None), analyze() compatibility alias; classical run_shots is separate. |
| Result | num_qubits, sample(shots,seed=None,max_outcomes=65536,wires=None), evidence(bits,paulis), verify(...), visualize |
| Result.math | statevector(max_bytes=64 MiB), amplitude(bits), probability(bits), probabilities(max_outcomes=65536), marginal_probabilities(wires,max_outcomes=65536), explain_probability(bits), table(bits=None,max_rows=16), norm(), fidelity(target), entropy(partition,max_rank=256,max_bytes=64 MiB), expectation(pauli), density_matrix(wires), purity(wires), observable(terms), conditional_probability(event,given), schmidt(wires), trace_distance(target), variance(pauli), top_probabilities(k), dirac() |
| Result.test | normalized(atol), probability(bits,expected,atol), fidelity(target,minimum), entangled(partition,atol,max_rank=256,max_bytes=64 MiB), distribution(target,atol), expectation(pauli,expected,atol), state(target,ignore_global_phase,atol) |
| Circuit.test | equivalent(other,ignore_global_phase=False,atol=1e-9,max_bytes=16 MiB) |
| Circuit.debug | trace(max_bytes=64 MiB,max_steps=256), compare(reference,...), checkpoint(index,...), compare_checkpoints(reference,pairs,...) |
| Circuit.resources | summary(): immutable ResourceReport |
| Circuit.visualize | text(max_qubits=32,max_gates=512): native text drawing; svg(max_qubits=12,max_gates=64) for bound unitary circuits |

Keyword-only arguments follow the implementation signatures; byte sizes above are descriptive, not Python expressions. CheckResult.status is PASS, FAIL or UNSUPPORTED; require() raises on non-PASS, and bool(check) raises TypeError. Invalid inputs raise errors; ResourceLimit and UnsupportedOperation inherit ValueError.

## Limits and interpretation

- Bit labels and Pauli labels are ordered highest wire to lowest wire; marginal labels use the caller's wire order.
- Numeric angles are finite real radians. Native import is limited to supported canonical standard gates, no classical bits, parameters, layout or metadata. Native Python objects are trusted input, not a sandbox.
- Dense statevector payload is 16 * 2**n bytes. Trace covers at most 8 qubits and defaults to 256 steps. Equal-index comparison retains the conservative historical two-trace budget, but streams current checkpoints. Explicit alignment compares at most 32 supplied checkpoint pairs. Legacy operator equivalence covers at most 8 qubits and budgets two matrices (32 * 4**n bytes); metrics budgets three (48 * 4**n bytes). Neither bounds all temporaries.
- Dictionary materialization has an explicit default cap of 65,536 potential outcomes. Full sampling uses the smaller of shots and state dimension for this conservative bound; marginal sampling first bounds the selected probability dictionary. Callers may explicitly increase the cap. None of these estimates bounds total RSS or every temporary allocation.
- Result retains accepted amplitudes within the normalization tolerance. Norm and amplitudes report stored values; Born probabilities, Pauli expectation, sampling, distribution distance, entropy and fidelity normalize their calculations by the state norm. State residuals compare stored amplitudes. Pure Result has no intermediate measurements; optional dynamic execution is separate. No hardware support.
- JSON replay: schema 1, 1 MiB, 22 qubits, 10,000 gates, strict keys. Producer metadata is informational; no cross-version deterministic guarantee.

## Typing
The installed package ships a PEP 561 marker and public API stubs. CI checks a strict typed consumer, including intentional invalid calls. Runtime checks still reject invalid values that static types cannot distinguish (e.g. bool as an integer).

Additional guards: exporting a dense snapshot copy is bounded by its payload; entropy bounds the smaller Schmidt dimension and matrix payload before SVD; drawings have logical gate/qubit caps; sampling rejects shot counts above signed 64-bit range. These are not guarantees about LAPACK workspace, drawing output length, native temporaries or RSS.

Experimental logical transpilation delegates to Qiskit at optimization level 0 with only a supported basis and seed. No target, coupling map or backend; rejects layout/unsupported output and verifies strict full-operator equivalence up to 8 qubits. This can be expensive and is not a QPU optimization guarantee.

For distribution boundaries and licensing review see [third-party review](third-party-review.md). The package is not published.

## Experimental developer extensions

See [SDK roadmap](sdk-roadmap.md) for direct gate aliases, the expanded gate registry, initial states, selective inspection, verification, density matrices, parameter binding and algorithm contracts. Existing `.gates` remains supported.

- `Result.visualize.histogram(k=8)` returns SVG text; bars are actual probabilities, with omitted mass shown. `bloch(wire=0)` returns reduced-state coordinates.
- `Contract(n, probabilities=..., expectations=..., normalized=..., atol=...)` is immutable; `verify(result)` returns a typed report without simulation.

### Advanced experimental extensions

- `Circuit.symbolic(n)`, `Circuit.parameter(name)`, `parameters`, `bind(mapping)`: explicit native symbolic construction and complete binding, with unbound operations rejected.
- `mcx(controls,target)`: 1–7 closed controls; CX/CCX canonical for one/two controls.
- `phase_estimation(phase,precision=3)`, `simon(secret)`, `teleportation(theta,phi,verify=False)`: bounded teaching circuits, not general algorithm solvers.
- `Circuit.classical(n,num_clbits)`, `measure(wire,bit)`, `reset(wire)`, `if_x/if_z(wire,bit,value=1)`, `run_shots(shots=1024,seed=None,max_bytes=...)`: local native Aer optional extra. One register, no unitary run, replay, trace or transform. `ShotResult.counts` defensive dict, `probabilities()` empirical frequencies.
- `Circuit.visualize.svg()` and `Result.visualize.bloch_svg(wire=0)` return bounded SVG schematics. The former supports bound unitary circuits only.

- `Result.math.observable_variance(terms,max_bytes=...)`: real weighted Pauli sum, dense native matrix, eight-wire cap; variance is the squared norm of the centered operator applied to the normalized snapshot. Not a general mixed-state calculation.

### Experimental verification engineering

See [R01–R15 contracts and limits](verification-roadmap.md) for capabilities, operator metrics, compare/diff, Evidence, checkpoint contracts, StatisticalContract, QueryPlan and the optional QCEC adapter. All costly operations are explicit.

## Pre-alpha behavior guide

See [verification guide](verification-guide.md), [mathematical conventions](mathematical-guide.md) and [known limitations](known-limitations.md). Canonical examples use fluent gates; `.gates` and `.analyze()` remain compatibility surfaces. `analyze()` executes the default zero-input simulation explicitly. `copy()` and bound transforms return independent circuits. `capabilities` describes structural eligibility, not installed backend availability or resource sufficiency.

## Progressive Python conveniences

See [language guide](language-guide.md) for typed dictionary reports, ordered single-wire batches, named selections, apply, checkpoint labels, local Pauli mappings, named binding, bounded sweeps, decoders and reversible composition. No implicit simulation or new execution model.
