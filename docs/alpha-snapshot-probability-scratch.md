# Snapshot probability scratch — #91

Baseline 72187710ff7969d64f7cfda023246448ce075c83. No new public API, budget,
state ownership or output schema. All preflight occurs before numerical work
as before.

- Full and marginal probabilities: square and normalize the fresh real
  magnitude buffer in place. Marginal axis order and reduction unchanged.
  This does not guarantee less peak allocation on NumPy versions that already
  reuse temporaries; the marginal transpose/reshape may still copy.
- Distribution TV distance: normalize two fresh real buffers, subtract and
  take absolute value in place; preserve both reductions, normalization
  by each distribution sum, tolerance and report. Neither input is mutated.
- Fixed/legacy paths: Result construction converts caller-supplied input to
  complex128 then validates and copies; no public budget. Fidelity and state
  comparison may construct a defensive Result from raw targets; distribution
  requires an existing Result and checks width and tolerance first. Conditional
  probability may copy a strided slice via ravel; top-k output <=65536 but
  scans all amplitudes; norm uses a state reduction. Table, dirac and evidence
  cap selected outputs but not full native state work. Existing caller/native
  allocation boundaries stay explicit, not a process RSS guarantee.

Local isolated numeric diagnostic (NumPy 2.3.5, seed 42, 9 timing repeats,
fresh complex arrays and inputs excluded from traced allocation, no installed
SDK or Qiskit). Previous/current expressions returned identical results
for 12, 16 and 20 qubits. TV tracemalloc peak MiB: 0.157/0.064, 2.000/1.001,
32.000/16.001. TV median ms: 0.024/0.023, 0.260/0.249, 8.049/5.154.
Full probability vector peak MiB: 0.063/0.031, 0.500/0.500, 8.000/8.000.
No universal memory/speed claim: this is numeric-expression allocation
tracking, not isolated process RSS or an end-to-end dictionary benchmark.

Tests compare exact former NumPy expressions across widths, ordered marginal
axes, slightly non-unit norms accepted by Result, self/other comparisons,
unchanged inputs and rejected resource/tolerance requests before magnitude
allocation. Full CI required before merge. Dedicated-host #100, exhaustive
native allocation accounting, and final integration remain separate.
