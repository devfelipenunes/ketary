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
