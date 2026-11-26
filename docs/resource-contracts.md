# Resource and ownership contracts

The following describes existing public limits; it does not introduce new caps.
Statevector payload is 16*2^n bytes. Operator payload is 16*4^n bytes per
matrix. These estimates exclude native scratch space, input conversion,
Python objects, serialization, allocator fragmentation and child processes.

| Path | Work / retained data | Preflight and caveat |
|---|---|---|
| Circuit.run | Gate evolution, one returned snapshot | State payload cap before native execution; temporary arrays extra |
| Bound batch / apply | Validate incoming selections/angles; append standard gates by native broadcast or ordered scalar calls; compose bound blocks | No whole-prefix or staging-circuit copy for ordinary bound gate batches; suffix rollback on native error; self-application copies source, unitary symbolic gate batches also use suffix rollback; symbolic composition uses the same preflighted suffix transaction; classical batches stage a native copy |
| Result.math.expectation | One native Pauli query over existing state | No implicit simulation; full-state work |
| Observable / aggregate | Up to 256 terms per observable, up to 32 predicates | Up to 8192 Pauli evaluations; no aggregate time guarantee |
| Density / Schmidt | State-sized input and output, matrix work | Existing separate payload/rank bounds, not scratch/RSS |
| QueryPlan | Exactly one simulation; selected dense outputs | Sum state and matrix payload estimate; Python real/imag lists add overhead |
| SweepPlan | Up to 32 privately retained bound native circuits and result snapshots | Complete finite rows preflight once; each native assignment still checks evaluated values and phase; aggregate snapshot payload preflight, not total peak RSS |
| Trace / compare | Prefix state evolution, bounded retained states | Existing conservative budgets unchanged |
| External QCEC | Optional backend worker | Deadline and width/gate limits, not child RSS |

Use targeted queries rather than enumerating whole distributions. Record
execution counts and raw memory/timing data, not inferred process memory.
Do not silently lower existing accepted caps or change schemas. Any new
resource policy requires compatibility review.

## Ordered wires

New canonical ordered-wire inputs use list, tuple, range or ordered
generators. Output labels follow the supplied sequence, not sorted wire
indices. Full-width labels remain highest-wire-first. compose/apply/append
and fluent batch/registered selections reject unordered containers.
Legacy h_many, mcx and subsystem queries (including QueryPlan) retain
their existing iterable acceptance; no deterministic ordering is promised
for unordered containers. This is a documented compatibility exception,
not a recommendation. A future rejection requires owner-approved migration.

## Ownership and concurrency

Circuit is mutable, including annotations. Do not mutate a circuit
concurrently with any execution, composition or inspection on it.
No thread-safety/reentrancy guarantee, internal locks or automatic workers
are provided. Use independent copies per caller and coordinate access
externally. Results defensively own snapshot arrays; exported native
objects and dictionaries are caller-owned copies, except report dicts
themselves are mutable legacy records. No implicit cache or rerun.

Repeated/placed composition preflights 10,000 placements and 100,000 appended operations on new expansion paths. This bounds instruction count, not native peak memory. Grouped math preflights 1..32 requests and unique-label state entries against max_work=64*1024**2 by default. This is a workload proxy, not a byte or timing guarantee. Legacy one-block application remains uncapped by the new expansion ceiling.

PERF04–06: private trusted unitary evolution borrows read-only Result input and adopts only a fresh, owning contiguous native output; aliasing or view outputs are copied. Public construction/export remains defensive. Complete binding of a validated internal circuit checks bound numeric values; external from_parameterized continues full structural validation. SweepPlan freezes independent bound native circuits rather than serializing/replaying JSON; it retains the same row, width, operation and aggregate state-payload caps. No native simulator or public schema change.

Exact commuting evolution retains <=8 wires, <=256 terms and <=10,000 estimated appended gates. Symbolic time uses one native block and the preflighted suffix/phase transaction; no implicit execution or approximation. Binding retains finite real checks for evaluated gate angles and global phase. Exact Python floats use a finite-only scalar validation path; other numeric types keep the established conversion and rejection rules.

QueryPlan validates the bounded logical replay at construction and retains an independent private native-backed Circuit plus immutable estimate scalars. The original logical payload remains for equality and compatibility; retaining both costs additional memory not covered by state/density payload budgets. Runs do not reconstruct or mutate the private snapshot; source and exported report mutations cannot affect subsequent runs. No result caching or shared mutable concurrency guarantee. Preparation now includes one replay; compare amortized costs and measure RSS separately.

Streamed observable variance uses bounded little-endian Pauli permutation/parity chunks when the existing four-state payload budget accommodates conservative chunk scratch. The old native one-wire path remains for the smallest admitted budget. No change to accepted budget, maximum work, normalization, output, or public signature. Scratch estimates exclude total RSS; all terms are validated before numerical work.

Basis factory: 1..62 wires, at most one X per wire, no state allocation until explicit execution. Expectation Jacobian: <=8 wires, <=32 parameters, <=256 source instructions, <=64 active symbolic occurrences, 1..8 real observables. Up to 128 validated shifted native circuits retained temporarily (<=32768 source-sized instructions), at most 128 ideal simulations, three state payloads preflighted; circuit storage, grouped Pauli work and scratch are not RSS. No cached state, automatic optimizer or state derivative. All inputs, binding and shifted circuits preflight before simulation.

DX coverage: from_symbolic <=62 wires, 10000 gates, 4096 parameters; bind_partial only accepts native identities and revalidates output. from_synthesized/control: trusted local bound gate-only input, <=5 total wires, <=256 source instructions, <=10000 output instructions, strict full operator residual <=1e-9. Native definition expansion/synthesis scratch is not bounded RSS. Product evolution: <=8 wires, <=64 steps, first/second order, <=10000 conservative expanded instructions; explicit approximation, no accuracy guarantee. Pauli algebra <=4096 term pairs, <=256 output terms; complex products stay native.

DX execution candidates: from_dynamic admits <=12 wires/bits, <=1024 top-level and expanded instructions, disjoint contiguous classical register partition, native standard gates, measure/reset and bit/register equality if/else up to three conditional levels, with gate-only leaves. Counts normalize register separators without changing native memory bit order; source registers preserved. No loops, expression conditions, variable captures, conditional measurement or conditional reset. run_density and run_noisy return native DensityMatrix, <=8 wires, <=1024 instructions, three density payloads (3*16*4**n bytes) preflight, not RSS. Noise requires optional native Aer NoiseModel, zero initial state, no measurement; no hardware claims. transpile_for returns native target circuit, <=12 logical wires, <=1024 instructions; no submission or output layout reimport. Target width/compilation costs depend on caller backend.

Dense preparation/matrix/exact evolution: <=5 wires (32 amplitudes/32x32 matrix), bounded ordered iterable ingestion, finite scalars, normalized states and unitary matrices, no reset or implicit normalization. Native checked synthesis retains <=10000 output instructions and strict full-operator residual <=1e-9. Dense HamiltonianGate computes exp(-itH) for real Pauli sums, including noncommuting terms; floating-point synthesis is numerical, not a formal certificate or a general error bound. Dynamic execution revalidates expanded instructions after builder edits and before optional native execution; cap 1024 across top level plus all branch bodies.

Explicit run_channel: full-width standard native Kraus CPTP map after ideal circuit evolution, <=4 wires, 1..16 matrices, same input/output qubit dimensions; all finite and copied, complete positivity/trace preservation checked before execution. Budget includes 3 density payloads plus Kraus matrix payloads, not native scratch/RSS. No Aer, measurements or channel insertion during arbitrary gate sequences. expectation_complex: full-width native SparsePauliOp, <=256 incoming terms, finite complex coefficients and bounded Pauli-state work; real Hermitian expectations/contracts unchanged, no execution or dense operator materialization.

Controlled rotation Jacobian: CRX/CRY/CRZ generator gaps 1/2 and 1 require four shifted circuits per active occurrence; two-point gates unchanged. Mixed total at most 128 shifted circuits, so <=32 all-controlled occurrences or <=64 all-two-point occurrences. All shifted circuits validated before execution. No arbitrary generator or state derivative.

Pauli duplicate import and product aggregation retain up to 4096 finite complex contributions temporarily (bounded by the existing incoming/pair limits). Real and imaginary sums use compensated fsum; nonfinite products or overflowing sums fail explicitly. Output-term caps unchanged.

Nested dynamic import validates every branch, including unreachable alternatives, under a single 1024-node count and maximum conditional depth three; conditions reference the immediate block's instruction operands, and body widths must match. All measurement provenance remains top-level. Existing native target bridge remains local only.

Quantum geometric tensor: ideal pure state only, <=8 wires, <=16 native parameter identities, <=256 source instructions, <=32 active occurrences, <=64 validated shifts plus one base run. Preflight counts 2*parameters+8 state payloads; bounded 16x16 result and native circuit copies/scratch excluded from payload RSS. Projected derivative matrix, never dense projector; global phase derivative omitted only because projection removes it. Unsupported generators fail before simulation; empty parameter order returns empty tuple after valid binding.

Expectation Hessian: <=8 wires, 8 parameters, 256 source gates, 8 active symbolic occurrences, 8 observables and 256 unique shifted native circuits. Each circuit validated before execution; three state payloads, circuit copies and bounded classical coefficient tables are separate costs (not RSS). Returned immutable tensor is observable/parameter/parameter order, symmetric by construction. Unsupported generators, nonfinite expressions and overflow reject; no finite differences, automatic optimizer or general generator guarantee.

Local run_channel(..., wires=...) maps local bit i to the i-th explicitly ordered distinct wire, at most four selected wires on a circuit of at most eight wires. Omitting wires preserves the existing full-width <=4 contract. Budget includes three full density payloads plus the local Kraus matrices, not expanded full-width Kraus or native scratch/RSS. Caller may compose trusted native Kraus channels before execution; final standard CPTP input remains subject to the 16-matrix cap.

Explicit project_annotated(template) returns (ideal logical Circuit, independent native QuantumCircuit snapshot). Bound <=22 wires/10000 instructions, standard gates and canonical barriers only; no layout, classical bits, captures or variables. Metadata exact JSON builtins, <=8 depth, <=4096 visited nodes (keys included), strings <=4096 characters, finite float, <=64-bit integer, <=64 KiB UTF-8 JSON. The native source preserves annotations, registers, gate order, barriers and global phase; the projection intentionally drops native metadata, name/register layout and barriers for ideal operator math. No synchronization of outputs, serialization of native source, scheduling equivalence, arbitrary object deepcopy or trust of untrusted QPY. Existing from_qiskit strict unchanged.

Grouped real and native complex expectations now reuse one call-local native
Statevector handle across sorted unique Pauli labels, after existing full
preflight. The handle borrows the immutable Result array; it is not stored
or exposed, no implicit circuit execution or persistent result cache.
Numerical finite/imaginary checks and normalization/clipping policy are
shared with the single-label path. Existing bounds, compensated sum,
label order and public signatures are unchanged.

Derivative planners share a private call-local shifted-native-copy helper;
all shifts retain the existing per-method preflight, full native validation
and independent ownership. No additional state payload, caching, native
execution or change to shift count, gate budget or formula.

Scalar native Pauli expectations retain finite/imaginary validation and
normalize by the stored squared norm, then use scalar comparisons to clip
to [-1,1] with signed zero preserved. No change to work, memory, native
math or public contract. See [scalar Pauli clamp](scalar-pauli-clamp.md).
