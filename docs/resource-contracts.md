# Resource and ownership contracts

The following describes existing public limits; it does not introduce new caps.
Statevector payload is 16*2^n bytes. Operator payload is 16*4^n bytes per
matrix. These estimates exclude native scratch space, input conversion,
Python objects, serialization, allocator fragmentation and child processes.

| Path | Work / retained data | Preflight and caveat |
|---|---|---|
| Circuit.run | Gate evolution, one returned snapshot | State payload cap before native execution; temporary arrays extra |
| Bound batch / apply | Validate/stage incoming operations, append to native program | No whole-prefix Ketary copy on ordinary bound path; self-application copies source, symbolic/classical batch retains old path |
| Result.math.expectation | One native Pauli query over existing state | No implicit simulation; full-state work |
| Observable / aggregate | Up to 256 terms per observable, up to 32 predicates | Up to 8192 Pauli evaluations; no aggregate time guarantee |
| Density / Schmidt | State-sized input and output, matrix work | Existing separate payload/rank bounds, not scratch/RSS |
| QueryPlan | Exactly one simulation; selected dense outputs | Sum state and matrix payload estimate; Python real/imag lists add overhead |
| SweepPlan | Up to 32 bound result snapshots | Aggregate snapshot payload preflight, not total peak RSS |
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
