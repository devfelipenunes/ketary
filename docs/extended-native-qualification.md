# PERF19–26: native coverage and qualification

The BENCH07 exact head ec870c0f9ff5c9ada8dda1ac127681a6342d9bbf
passed all nine ablation jobs and six SDK jobs. Source:
https://github.com/devfelipenunes/ketary/actions/runs/45766023430 .
Upper median of per-case paired forced/direct ratios, separated by runner:
algorithms (20 of 36 direct) 5.744, 5.590, 5.567;
gates (22 of 60) 9.111, 9.097, 10.101;
corpus projections (5 of 12) 13.180, 12.107, 10.340.
All 282 supported case/input/runner comparisons had direct median latency
less than original Qiskit Statevector. These are shared CI observations,
not universal speed or direct coverage claims. BENCH05 and BENCH07 merged
at ba5097e838c9347a557e821608efcca1e6bb3f43 and
42ae366a7522e16912a401d581eacf061c849261 respectively.

## Eight priorities and evidence gates

1. Direct execution: keep the strict 11-gate ablation and its rejections.
   Extended native standard gates CP/RZZ/CCX avoid forced decomposition
   only if native pack and full mathematical tests pass.
2. Prepared programs: explicit read-only bytes-backed topology snapshots.
   Preserve authoritative Qiskit circuit and no hidden caching.
3. Copies: native output is allocated once in Python and passed to the
   private Result._from_evolution ownership gate. Compare identical
   defensive public exports, including the original constructor path.
   Input and register transfers remain necessary; no zero-copy claim.
4. Register reuse: allocate once per explicit batch and reset input for
   each independent row. Retained output <=128 MiB and angles <=64 MiB.
5. Gate coverage: separate v2 row layout (opcode, arity, 22 wires) with
   exact class checks in Python and native gate-kind checks in C API.
   MCX is explicit Python packing only; no hidden fallback. Preserve the
   existing 8/11-gate ABI and benchmark results.
6. Fusion: #83 implements adjacent involution/rotation experiments.
   Do not fuse parameter expressions or reorder gates without oracles.
7. SIMD/cache: same-runner portable vs -march=native, counterbalanced
   order, raw timings, host cache/ISA manifest and bridge disassembly.
   Optional perf stat process-wide counters only when authorized/available;
   no inference of kernel SIMD from compiler flags or process counters.
8. GPU/MPI: existing hardware diagnostics workflow 45763839078 passed
   CPU and local MPI jobs. GPU/cuQuantum/multi-node remain unvalidated.
   Run the documented explicit hardware probe only on an authorized
   equipped machine. No CPU fallback may be labeled GPU.

## Exact operations

CP uses applyTwoQubitPhaseShift; RZZ uses applyPauliGadget with ZZ;
CCX and MCX use applyMultiControlledPauliX with ordered controls and
target. All from pinned QuEST operations.h:
https://github.com/QuEST-Kit/QuEST/blob/9d7618d7263e3bfba433b88cf1eac0647f08fa0a/quest/include/operations.h .
Test every basis vector in five-qubit cases with spectators and nonzero
phase, random complex state, unsupported/custom/open controls, aliases,
and repeated calls. No tolerance relaxation. Raw topology width costs
are retained (96 bytes per gate plus angle); performance is not assumed.
Benchmark 24-gate CP/RZZ/CCX/MCX workloads and compatible algorithms
against explicit 11-gate lowering with qubits_initially_zero=False.
Compare preparation-inclusive, prepared/copy, prepared/adopt, and batch
paths. Fixed CPU double precision, no automatic backend or fallback.
The #83 research remains independent; no public SDK API change.

## Dedicated-host qualification

Use existing research/quest_hardware and hardware_performance.py with
explicit CPU/GPU/MPI modes on an authorized machine. Record driver,
GPU and VRAM, compiler, build flags, CPU affinity, ranks, thread counts,
QuEST commit, raw stage latencies, output errors and exclusions. Compare
same workload and output contract, not across unrelated machines.
Dedicated device was offline at the present inspection. Do not claim
CUDA/cuQuantum execution, peak bandwidth, GPU memory, multi-node scaling,
or release validation before actual artifacts exist.

See [native backend decision](native-backend-decision.md) for the consolidated evidence and NO-GO promotion gates. This does not authorize native backend integration.
