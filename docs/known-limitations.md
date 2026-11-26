# Known limitations (pre-alpha)

The [capability matrix](capability-matrix.md) consolidates current supported
routes and their boundaries. [Resource contracts](resource-contracts.md)
remain authoritative for detailed budgets, ownership and preflight.
[Production qualification](production-fronts.md) tracks evidence separately.

- Python 3.12.x only, Qiskit pinned. Linux is the routine CI target; earlier
  full Linux/Windows/macOS qualification passed on #365, not the latest tree.
  Experimental API; no stable 1.0 or published-distribution guarantee.
- Strict from_qiskit admits bound standard logical gates, not arbitrary
  instructions, layout, metadata or barriers. Explicit native synthesis,
  symbolic import and annotated projection are different routes; no silent
  lossy import. Logical replay: <=22 wires, <=10000 operations, <=1 MiB;
  no general symbolic replay or arbitrary native-object serialization.
- Dynamic mode requires optional Aer. Explicit from_dynamic accepts multiple
  contiguous classical registers, gate-only conditional bodies to three
  levels, top-level measurement/reset, <=12 wires/bits, <=1024 instructions
  including all branches, <=10000 shots. No loops, arbitrary expression
  conditions, variable capture, conditional measurement/reset or conversion
  to a pure state. Logical resource summaries are not runtime cost estimates.
- Result represents an ideal pure snapshot. run_density/run_noisy return
  native DensityMatrix; run_channel applies a bounded final CPTP map after
  ideal evolution. No arbitrary noisy mid-circuit channel execution.
- Exact dense preparation, unitary/control synthesis and noncommuting
  evolution are restricted to <=5 total wires and checked full operators
  (component tolerance 1e-9). Native synthesis can fail; no silent tolerance
  relaxation. Product evolution is an explicit approximation, not a
  certified floating-point error guarantee.
- Observable is a real Hermitian Pauli sum; complex products and commutators
  return native SparsePauliOp. Complex expectation is an explicit separate
  route. No arbitrary symbolic predicate language or general generator.
- Dense operator comparisons <=8 wires; selected-input witness comparison
  <=12 wires/256 gates; external QCEC <=22 wires/256 gates with deadline and
  separate optional installation. Numerical or statistical reports are not
  formal certificates. Witness minimization does not establish root cause
  or global minimality.
- Named selections/checkpoints are local; replay preserves supported logical
  operations, not names. project_annotated returns two independent objects:
  ideal logical projection and preserved native snapshot. No synchronization
  or scheduling equivalence guarantee. Report dictionaries retain legacy
  mutability; native exports and Result snapshots are defensive.
- Payload budgets are not process RSS guarantees. Native scratch,
  serialization, Python objects and child processes add costs. No thread
  safety or concurrent mutation guarantee. Sweeps are bounded ideal local
  simulations, not hardware jobs. transpile_for is a local native target
  handoff, not physical execution or verified hardware compatibility.
- CI benchmarks and authored defect/application corpora are preliminary
  evidence. Dedicated-host benchmarking, independent participant studies,
  legal/notice review and release approval remain outstanding.
