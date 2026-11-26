# Alpha chunking and architectural boundaries — candidate

Research-only; refs #190 #303 #310 #90. Keep public Circuit/Result/Observable/
Contract unchanged. No new installed module, simulator, API or resource cap.

* CH01: vary the existing Pauli accumulation kernel's chunk size. Retain
  normalized input, full action output, reduction and term order. At 18
  qubits the baseline budget admits all tested sizes; do not reinterpret
  max_bytes as process RSS. The current runtime caps chunks at 4096 and
  retains a native fallback for a tight budget. Larger sizes are exploratory.
* CH02: vectorized local selection plus bounded merge for top-k. Candidate
  ranks using vectorized complex magnitudes; exact scalar ties and near ties
  require independent qualification. Record disagreements instead of hiding
  them. Not a drop-in implementation until ranking is proven compatible.
* CH03: ordered-wire bit projection and bincount per block. Compare with
  existing transpose/reshape/sum, independent scalar reference and reversed
  wire order. Retain requested output width; roundoff can differ.
* CH04: sweep and trace retain public complete outputs. Reuse #468/#473/#475;
  do not change retention or split preflight until their exact-head results.
* CH05: detect connected wire components on bound logical gate circuits.
  Global phase, entangled input and cross-component gates prevent naive
  independent simulation. Structural detection only; no factorized execution.
* AR01–03: research kernels are separate from profiling/orchestration.
  Move a measured cohesive kernel into the installed SDK only with ADR,
  updated ownership/import inventory, compatibility and exact CI; avoid
  cosmetic splitting of Circuit, Result and ergonomics.

Benchmark 3 seeds, 5 randomized repetitions, widths 10/14/18, chunk sizes
256/1024/4096/8192 when bounded by fixture length, same-state results.
A separate Linux process per route at 18 wires measures lifetime peak RSS
before/after the timed operation; not incremental allocation or dedicated
host evidence. Retain raw samples, p50/p95, negative outcomes and exact
ranking equality. A large-state improvement cannot justify a regression
or semantic change in small states. Test near-tie adversarial inputs before
runtime promotion. No general speedup claim. Research should not compete
with an unbounded number of additional PRs.
