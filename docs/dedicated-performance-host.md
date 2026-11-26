# Dedicated performance host harness

OPT14. This harness is an explicit operator-run protocol, not a CI job,
host provisioner or attestation service. An authorized isolated Linux
host with the pinned Python 3.12 environment and research toolchains
(C++ and Rust) must be supplied. No release or result is implied.

Inspect the plan without executing any benchmark:

```sh
python -m research.dedicated_performance_host --plan
```

After following release-validation.md and ensuring a clean checkout,
stable host and no competing workload:

```sh
python -m research.dedicated_performance_host \
  --acknowledge-isolated-host --output /absolute/new/results-directory
```

The harness records commit, CPU, RAM, affinity, environment, compilers,
thread limits, full test logs and three complete sets of thirteen
diagnostics, including explicit SIMD and process-tree memory. Output is
outside the checkout. All raw logs and JSON files are retained with
SHA-256 checksums and a manifest. A failed command stops qualification
and records incomplete status; a successful run is MEASURED_REVIEW_REQUIRED,
not production approval. Review each output's semantic status (including
UNSUPPORTED SIMD), p50/p95, variation and memory. The operator's isolation
attestation is not independently verified. Do not publish artifacts without
explicit authorization. No SDK behavior changes.
