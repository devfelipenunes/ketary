# Additional verified benchmark records — 2026-11-26

The [additional timing records](benchmark-additional-2026-11-26.csv)
contain 579 logged medians, with p95 when available. They cover
the initial longitudinal runs (276 records), standard
benchmarks at PERF01, EXP07, PERF04–06 and the integrated native research
candidate (272), and the combined Rust/QuEST audit
(31). The initial longitudinal smoke rows are explicitly
marked and not equivalent to the 30-repetition runs. Standard runs can
have internal baselines (e.g. dense vs streamed); check variant labels.
There is overlap in *workloads* with other studies, not identical trials.

[Standard memory diagnostics](benchmark-standard-rss-2026-11-26.json)
retain the original RSS reports. Linux high-water RSS includes process
overhead; it is not an allocator measurement.

[Published QASMBench correctness records](benchmark-corpus-correctness-2026-11-26.json) retain the measured correctness outcomes and excluded cases from the pinned unitary projection, not timing observations.

All records reference their original GitHub Actions jobs. Do not compare
absolute medians across different hosts as a paired gain. This supplement
does not convert the research C ABI or QuEST backend into a public API.

Current standard benchmark (PERF04–06): [job](https://github.com/devfelipenunes/ketary/actions/runs/45763889629/job/139720289329).
Combined native pipeline: [job](https://github.com/devfelipenunes/ketary/actions/runs/45764043293/job/139720548256).
