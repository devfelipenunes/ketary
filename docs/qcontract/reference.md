# Contract reference — candidate 0.1.0a3

All domains use the admitted ideal unitary gate alphabet H, S, Sdg,
X, Z, CX, T, Tdg. Canonical closed controls; no classical bits,
parameterized gates or nonzero source global phase. Input snapshot
1–64 wires, at most 100,000 admitted gates. Individual domain bounds
are stricter; logical max_work is 1–2,000,000, not a CPU/memory cap.
All batches have 1–64 obligations. See source validation for precise
limits; no arbitrary dynamic circuit support.

| Contract | Predicate/scope | Important limitation |
|---|---|---|
| Transition | U† B U = A, all inputs | Signed Pauli; phase insensitive |
| StateEigen | P U|0> = U|0> | Zero input only; signed Hermitian Pauli |
| CleanInput | U maps initially zero ancillas to clean output subspace | Other wires arbitrary |
| RelativeAction | Agreement of U and V on clean-input subspace, up to common phase | Admitted relative action methods |
| Equivalent | U and V agree up to global phase, or strict equality | Modulo phase <=32 wires, strict <=5 wires and <=512 gates each |
| Separable | Rank-one bipartition of U|0> | <=5 wires, <=512 gates |
| ZBranch | Probability and unnormalized expectation for specified Z outcome | <=5 wires, <=512 gates; no dynamic circuit |
| SumTransition | All-input equality of rational weighted Pauli sums | 1–64 terms, bounded exact rational coefficients |
| NoiseAfter | Equality after specified finite Pauli channel following Clifford circuit | <=16 mixture entries; not arbitrary CPTP |
| Correctable | Knill–Laflamme condition for finite error set and supplied stabilizers | Circuit-independent; no physical recovery guarantee |

Named(name, specification) works with all ten families. transition(),
invariant(), zero_input(), clean_ancillas() are convenience constructors.
A Plan is conjunction of independent obligations; it does not prove
sequential composition or arbitrary Hoare implication. Named labels
are human metadata, not part of mathematical obligation identity.

Pauli("IZ") uses highest wire first; pauli_on(width, ((0,"Z"),))
builds the same signed masks explicitly. Neither returned mask retains
declared label width. Check actual prepared width. Duplicate wire indices,
invalid axes, bools and out-of-range indices are rejected.

prepare(circuit) captures packed source snapshot; do not concurrently
mutate the source. Explicit preparation policies choose plain/weighted
DAG or fallback. Eligible Clifford state obligations in individual, homogeneous or mixed batches
can use tableau images if the per-item budget suffices. Other paths remain unchanged.
statuses() returns only exact status labels, no full report or witness.
verify() returns immutable report objects; require() rejects unresolved
as well as refuted results.

Status: PASS exact property holds in admitted domain, FAIL exact
refutation, INCONCLUSIVE no decision, UNSUPPORTED outside implemented
domain. Invalid input raises TypeError/ValueError rather than returning
a mathematical verdict. Evidence replay only for supported routes.
