# Historical performance scorecard (2026-11-26)

[Machine-readable timing table](historical-performance-2026-11-26.csv): 1046 verified timing rows extracted from successful workflow logs. Each row includes the original job URL and comparison scope. Counts: revision: 435; high_level: 120; hot: 90; engine: 270; capi: 15; hardware: 108; mpi: 8.

This is an index of logged medians and p95 where available, not a substitute for raw artifacts. Empty p95 means not extracted from the logs. Different runner replicates must not be pooled or compared for thread scaling. Native kernel-cycle and end-to-end timings are distinct. The revision comparison covers pre-PERF01 vs pre-PERF04–06; the hot-path comparison covers pre- vs post-PERF04–06. The C ABI and QuEST results are research prototypes, not the default SDK API. The high-level results predate the hot-path optimization. Sources are successful exact-head workflow runs; the CSV records benchmark variants and not unsupported cases. Raw distributions, host/environment manifests, memory and correctness details remain in the linked run artifacts.

## Run index

- [Paired revision + high-level](https://github.com/devfelipenunes/ketary/actions/runs/45762354743)
- [Hot paths](https://github.com/devfelipenunes/ketary/actions/runs/45763889674)
- [Native execution engines](https://github.com/devfelipenunes/ketary/actions/runs/45763238221)
- [Qiskit C API](https://github.com/devfelipenunes/ketary/actions/runs/45763385582)
- [Hardware / local MPI](https://github.com/devfelipenunes/ketary/actions/runs/45763839078)

Do not infer general SDK superiority from selected workloads. See the new algorithm matrix for matched logical circuits, explicit common-basis lowering and peak RSS in separate processes.
