# Controlled-host closure preparation (R/P)

Refs #74 #86 #100 #101 #102 #245 #302 #309 #310. The new sampling runner is
a reproducible local diagnostic, not proof of an isolated or dedicated host.
Run on authorized Linux with Python 3.12 and pinned dependencies:
`python -m research.closure_sampling_pinned`. Retain raw JSON and exact
revision. Each observation is a separate process, pinned to one allowed
CPU, with thread variables set before import. The historical path uses the
same private immutable state snapshot, not a public copy. State and dense
scratch payload estimates exclude allocator fragmentation. RSS is Linux
process high-water, and setup may dominate; a zero increment is not zero
allocation. Raw count order, seed, width, depth and retained outcomes match.

## Outstanding independent host gates

- Record CPU model/ISA/cache, physical cores, affinity, compiler and binary
  hashes, OS/kernel, memory, power policy, competing load, environment and
  commit. Obtain authorization and verify isolation outside the benchmark.
- Counterbalance portable/native builds and 1/2/4 threads; inspect actual
  kernel disassembly and permitted counters. Compiler flags are not SIMD proof.
- GPU: explicit authorized device, no CPU fallback; synchronize transfers and
  kernels, retain VRAM peaks, driver/runtime/device identity and strict
  amplitude oracle. MPI: record rank/host topology and cross-node transport;
  same-host MPI is not multi-node qualification.
- Run matched raw repeated measurements, record failures and negative results.
  Do not mark dedicated hardware work complete based on shared CI or plans.
- Legal/name review and independent participants are separate release gates.
  No release or external execution is authorized by this document.
