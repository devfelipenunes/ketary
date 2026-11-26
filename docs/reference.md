# API reference (experimental L0)

The public import is `import ketary as q`. All factories return Circuit.

| Surface | Methods and behavior |
|---|---|
| Factories | Circuit(n), bell(), ghz(n), constant_oracle(n,value=0), parity_oracle(mask,offset=0), deutsch_jozsa(oracle), from_qiskit(qc) |
| Circuit.gates | h,x,y,z,s,sdg,t,tdg(q); rx,ry,rz(theta,q); cx,cz,swap(a,b); ccx(c1,c2,t). Mutate and return Circuit. |
| Circuit | num_qubits, append(gate,wires) mutates; compose(other,wires=None), inverse(), decompose(reps=1), optimize(), to_qiskit(), to_json(), Circuit.from_json(payload) do not mutate source. Decompose only lowers SWAP. |
| Execution | run(mode="statevector",max_bytes=64 MiB), analyze() experimental alias |
| Result | num_qubits, sample(shots,seed=None,max_outcomes=65536) |
| Result.math | statevector(), amplitude(bits), probability(bits), probabilities(max_outcomes=65536), marginal_probabilities(wires,max_outcomes=65536), explain_probability(bits), norm(), fidelity(target), entropy(partition), expectation(pauli) |
| Result.test | normalized(atol), probability(bits,expected,atol), fidelity(target,minimum), entangled(partition,atol), distribution(target,atol), expectation(pauli,expected,atol), state(target,ignore_global_phase,atol) |
| Circuit.test | equivalent(other,ignore_global_phase=False,atol=1e-9,max_bytes=16 MiB) |
| Circuit.debug | trace(max_bytes=64 MiB,max_steps=256), compare(reference,ignore_global_phase=True,atol=1e-9,max_bytes=64 MiB,max_steps=256) |
| Circuit.resources | summary(): immutable ResourceReport |
| Circuit.visualize | text(): native text drawing |

Keyword-only arguments follow the implementation signatures; byte sizes above are descriptive, not Python expressions. CheckResult.status is PASS, FAIL or UNSUPPORTED; require() raises on non-PASS, and bool(check) raises TypeError. Invalid inputs raise errors; ResourceLimit and UnsupportedOperation inherit ValueError.

## Limits and interpretation

- Bit labels and Pauli labels are ordered highest wire to lowest wire; marginal labels use the caller's wire order.
- Numeric angles are finite real radians. Native import is limited to supported canonical standard gates, no classical bits, parameters, layout or metadata. Native Python objects are trusted input, not a sandbox.
- Dense statevector payload is 16 * 2**n bytes. Trace covers at most 8 qubits and defaults to 256 steps. Comparison counts both traces. Operator comparison covers at most 8 qubits and budgets two matrices (32 * 4**n bytes).
- Dictionary materialization has an explicit default cap of 65,536 potential outcomes. Sampling uses the smaller of shots and state dimension for this conservative bound. Callers may explicitly increase the cap. None of these estimates bounds total RSS or every temporary allocation.
- Result retains accepted amplitudes within the normalization tolerance. Norm reports actual norm, Born probabilities use stored amplitudes; sampling, distribution distance, entropy and fidelity normalize their calculations. Small discrepancies can occur near the tolerance. No physical measurements or hardware support.
- JSON replay: schema 1, 1 MiB, 22 qubits, 10,000 gates, strict keys. Producer metadata is informational; no cross-version deterministic guarantee.
