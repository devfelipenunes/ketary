# Circuit writing and expressive API study

## External evidence (exploratory)
- [QASMBench paper](https://doi.org/10.1145/3550488), [source commit](https://github.com/pnnl/QASMBench/tree/357b942396d5c2b7cbc1c229c585a6ef5ccaebac)
- [MQT Bench source](https://github.com/munich-quantum-toolkit/bench/tree/9d5a261030cd9f8178c26ec92b3a17d100c834e3)
- [Design patterns in quantum software](https://doi.org/10.1007/s00607-025-01467-2)
- [Mining Quantum Software Patterns](https://arxiv.org/abs/2601.06281)
- [Quantum Testing in the Wild](https://arxiv.org/abs/2501.06443)

16 purposively selected original QASMBench small files (paths in
research/qasm_source_inventory.py) were inspected at the pinned commit:
1,329 top-level statements; 412 adjacent same-name pairs. Source names
rz 433, cx 284, h 231, measure 74, u3 73, rx 69, y 56, x 32, sx 32,
ry 18, cu1 6, t 5, barrier 5, tdg 4, ccx 3, s 2, syndrome 1, cH 1.
h and cx occur in 13/16 files, measure 16/16. Counts include measurements,
barriers and custom invocations; no expansion of gate definitions/register
broadcast. Consecutive names do not imply equal angles or safe batching.
Not physical/transpiled frequencies, not representative population estimates,
not Python API usage. Reproduce with a user-provided pinned local checkout.
No third-party source is copied or executed in normal CI.

13 MQT Bench Python modules reviewed at the pinned commit: ghz, graphstate,
qaoa, qft, qnn, qpeexact, bv, simon, teleportation, vqe_real_amp, vqe_su2,
grover, wstate. Examples reveal directed chains, graph edges, rotation
layers, parameter vectors, repeated blocks, measurement and reset, and
dynamic control. This is a qualitative code review, not call-frequency mining.

## Authored controlled comparison
research/circuit_writing_study.py runs eight paired tasks inspired by these
families. Qiskit library factories are used for real amplitudes, efficient
SU2 and QFT, not deliberately inflated manual baselines. Other tasks use
direct native construction. Fixed angles and graph edges, <=4 qubits,
strict full complex operator comparison at 1e-10, including global phase.
No measurements in these unitary comparisons; not entire upstream programs.
Token counts exclude layout and comments; calls and loops are AST counts.
Report individual results, including cases where Qiskit is shorter.
Do not infer human productivity, readability or market differentiation
from authored examples. CI emits a machine-readable result.

## Candidate API from evidence
- chain/ring/star/all_pairs are pure bounded ordered logical pair generators;
  ring requires >=3 distinct wires; star starts at the first wire; all_pairs
  emits one orientation per combination. No hardware routing or scheduling.
- Circuit.wires is ascending range; rx/ry/rz/p accept aligned angle
  sequences for ordered distinct wires, same-length only; scalar broadcast
  unchanged. Validate entire sequence before mutation; no Cartesian
  expansion. Symbolic/classical retain staged copy semantics.
- Measurement grouping and symbolic parameterized block placement remain
  next design gaps, not implemented here. Existing unitary apply cannot
  compose unbound symbolic or dynamic blocks. Native ansatz factories
  may remain substantially more concise for common canned algorithms.

Next study: extend to held-out Python source projects (deduplicate, pin,
record selection/exclusion), count API call sites and semantic patterns,
include dynamic/measurement and parameter sweeps; compare completion time,
errors, and conceptual load with human participants. No performance or
adoption claim without controlled evidence.

The compact native baselines also use native pair broadcasting and repeat where supported. First CI revision passed the eight operator comparisons and 511 core/522 combined tests, but failed the exact public export inventory because four approved topology helpers had not been added to that separate assertion. Correct the expected explicit set (no weakening) and rerun all jobs before integration.
