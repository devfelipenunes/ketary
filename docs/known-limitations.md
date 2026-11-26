# Known limitations (pre-alpha)

- Python 3.12.x only; tested Linux CI, Qiskit pinned, no compatibility claim
  for other platforms/versions. API is experimental; no stable 1.0 promise.
- Bound unitary mode: standard allowlisted gates, closed controls, no arbitrary
  native operations, metadata/layout, unbound imports or hardware. Logical
  replay: 22 wires, 10000 operations, 1 MiB.
- Symbolic mode: native parameter expressions; complete binding required
  before unitary operations. No partial binding or symbolic replay.
- Dynamic mode: optional Aer, one classical register, X/Z conditional operations,
  12 wires/bits, 1024 top-level operations, 10000 shots. No generic control
  flow, external dynamic import, noise model or pure-state conversion.
  Logical resource summaries count top-level operations, not branch-expanded
  costs. Text drawing is available; unitary SVG is not.
- Result pure snapshots, no general mixed-state execution. Dense operator
  checks <=8 wires; witness comparison <=12 wires/256 gates; QCEC external
  adapter <=22 wires/256 gates with explicit deadline. QCEC is installed
  separately, not an automatically installed dependency.
- Payload budgets are not process memory guarantees. Native allocations,
  Python dictionaries, SVD workspaces and child processes can exceed them.
- Checkpoint comparison is zero-input; explicit alignment is caller supplied.
  Verification reports are numerical or statistical, not formal certificates.
- CI benchmarks and small authored defect adaptations are initial evidence,
  not independent research or proof of improved productivity.
- No published distribution; use a verified checkout or build artifact.

- Named selections/checkpoint annotations are local conveniences; logical replay preserves operators, not names. General controlled blocks and automatic ancilla cleanup are not supported. Sweep plans are bounded zipped ideal simulations, not hardware jobs. Typed report dictionaries retain mutable legacy behavior.
