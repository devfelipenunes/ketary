# Performance follow-up and dedicated-host acceptance

Refs #256 #305 #306 #307 #310. The single-item grouped path is distinct
from scalar expectation. Compare exact c97f8cf5 grouped and scalar method
bodies (before #377) with the candidate on the identical Result, with
patching outside timing. Three seeds at 4/8/12 wires, 30 paired raw samples,
independent scalar oracle. Repeat the #380 composition study three times
at each prefix (32/1000/10000); retain every p50/p95 and raw sample.
No timing assertion or runtime change. Do not conflate shared-runner
tail observations with controlled evidence.

## Dedicated host execution (not performed by this PR)

Use an isolated authorized Linux host as specified in release-validation.md.
Record actual CPU, RAM, compiler versions, CPU affinity, environment,
Python 3.12 and exact clean commit. Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS,
MKL_NUM_THREADS to 1. Install the pinned constraints and SDK. Run full tests
and retain logs. On the same host, retain three separate output sets for:

```sh
python benchmark.py --repetitions 30 > benchmark.json
python -m research.fluent_scalar_dispatch --output fluent.json --repetitions 30
python -m research.scalar_pauli_clamp --output pauli.json --repetitions 30
python -m research.batch_ingestion --output batches.json --repetitions 30
python -m research.trace_wire_index_rss --output trace-rss.json --repetitions 30
python -m research.performance_tail_and_singleton --output tails.json --repetitions 30
python -m research.native_finite_scan --output finite.json --repetitions 30
python -m research.explicit_sweep_parallelism --output parallel.json --repetitions 5
```

Use separate output directories for each run. C++ and Rust are research toolchain
requirements only, not SDK requirements. Compare medians, paired ratios,
p95, variation and isolated process high-water marks across runs. Record
aggregate process memory separately if evaluating multiprocessing; the
parallel experiment reports retained output payload only. No release
approval, host access, or benchmark result is implied by this protocol.
