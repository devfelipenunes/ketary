# QContract — Consolidation and performance roadmap (provisional name)

This document names the research initiative only. Repository/package/public
API names remain unchanged pending an explicit migration and namespace review.
Goal: a usable quantum specification and verification framework, adopting
well-established techniques rather than claiming novelty for their existence.

## Acceptance criteria

- Correctness before performance: independently checked exact outputs;
  numerical and exact results labeled separately; no speed comparison on
  unresolved obligations as though they were successful.
- Matched workloads and scopes; pin competitor versions, record seeds, gates,
  width, non-Clifford content, environment, setup, query and report overhead.
- Compare optimized competitor APIs, not only scalar loops.
- Distinguish cold end-to-end costs, prepared query costs, native-format and
  normalized-output costs. Record median, P95, raw samples and coverage.
- Prefer measured wins on a scoped domain; a loss is useful evidence too.
  Shared CI is screening, not a controlled benchmark or speed release gate.

| Epic | Deliverable | R32 status |
|---|---|---|
| C01 inventory | Map current research branches and 50 gate evidence to candidate | Existing ledger, update pending |
| C02 integration | Single maintained implementation with preserved legacy semantics | Batched facade dispatch submitted |
| C03 architecture | Explicit backend capabilities, selection and resource policy | Lookup opt-in; no automatic adoption |
| C04 semantics | Exact domain matrix and independent oracles | R31 domains passed; R32 parity submitted |
| C05 API | Usable immutable prepared API with predictable results | Private API only; public review pending |
| C06 algorithms | Representative full algorithms and mutant corpus | Earlier suites; broaden matched corpus |
| C07 performance | Best available Qiskit, Stim, QCEC baselines; fair comparison | Four R32 jobs submitted |
| C08 security | Strict FFI, bounded work, notice and vulnerability review | Packed admission submitted; audit pending |
| C09 distribution | Portable wheels and reproducible builds | R31 all three hosts identical locally; R32 candidate pending |
| C10 documentation | Installation, runnable examples and exact guarantees | Pending consolidated API |
| C11 science | Related work, reproduction, limitations, external review | Research references below, dedicated study pending |
| C12 alpha | Integrated tested artifact and compatibility decision | Pending merge/API approval |

## Technique adoption

- Qiskit PauliList vectorized Heisenberg evolution and Rust-accelerated
  Pauli propagation: compare vectorized baseline, not only per-Pauli loop.
  https://github.com/Qiskit/pauli-prop
  https://github.com/Qiskit/qiskit/blob/main/qiskit/quantum_info/operators/symplectic/pauli_list.py
- Stim inverse tableau and bit-packed stabilizer arithmetic:
  https://github.com/quantumlib/Stim
- MQT QCEC portfolio of decision diagrams, simulation and ZX rewriting:
  https://mqt.readthedocs.io/projects/qcec/en/stable/equivalence_checking.html
  https://github.com/munich-quantum-toolkit/qcec

These are external references and benchmark dependencies, not code copied
into the SDK. Evaluate licenses and scope before any integration. Pauli-prop
near-Clifford comparison is a follow-up; Qiskit dense expectations and
vectorized Clifford evolution are the R32 actual comparison paths.
QCEC full-unitary equivalence is not a substitute for individual contract
semantics. Consider ZX simplification only with independently verified
rewrites. No generic superiority or scientific novelty claim.

## R32 implementation and workload matrix

- Four-bit grouped ordered Pauli products in a persistent inverse tableau,
  optional lookup class. Up to 32 groups of 16 rows; trade memory and setup
  against dense-query speed. Packed 17-byte little-endian records reduce
  Python object allocation. Strict exact bytes, widths, signs and budgets.
- R30/R31 facade coalesces exact transitions only when each per-obligation
  slice can cover worst-case tableau query plus compact witness. Preserve
  independent budget exhaustion otherwise. No default lookup adoption.
- Exact suite: 12 partial/full widths, 128 images each, independent oracle,
  packed and tuple parity, mixed budgets and full facade report parity.
- Clifford: 4/16/32/64 wires, 256/4096 gates, sparse/dense observables,
  batches 1/64/1024, 48 cases, separate setup, tuple, packed output,
  Qiskit vectorized native output and normalized bytes, Stim loop.
  Full typed report batching vs individual reports at batch 64.
- State: 4/8/12/16/20 wires, GHZ and random brickwork, 8 observables each;
  native exact Heisenberg expectation and report against numerical Qiskit
  Statevector, prepared and end-to-end; track decisive coverage.
- Equivalence: 4/8/16/32 wires, Clifford and Clifford+T, equivalent and
  mutant pairs. QCEC and native full report; Qiskit Operator at <=8 wires.
- All R32 suites pending exact-head CI. No benchmark speed conclusions yet.

## Verified R31 baseline

Head 790463a492b1245bd1eb8598a57a7144389b6575, R31 run 46056380359:
4/4 jobs passed. Domain artifact records 192 checks. Three original
platform artifacts (Linux x86_64, Windows AMD64, macOS arm64) report
same-host byte-identical wheels and zero differing wheel members.
Windows /Brepro experiment resolved the R30 discrepancy on that runner.
Notices inventory has one missing local notice entry per platform:
editable project distribution ketary 0.1.0.dev0 (own project LICENSE
exists in source; installed distribution metadata issue still open).
No cross-host reproduction or legal clearance. R30 historical cancelled
workflow remains, so 29/30 returned exact-head workflows passed.
