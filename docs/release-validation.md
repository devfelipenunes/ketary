# SDK candidate acceptance and controlled benchmark

This is an internal pre-alpha candidate, not a released package. The required
GitHub validation verifies mathematical regressions, native probes, strict
typing, package installation, benchmarks and dependency inventories. Dynamic
execution is tested separately and together with the core.

## Dedicated host protocol

Use an isolated, authorized Linux host with Python 3.12, stable power settings
and no competing workloads. Record host CPU, RAM, OS, CPU affinity, exact commit
and installed packages. Do not infer dedicated-host performance from shared CI.
From a clean checkout:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -c constraints/linux-py312.txt -r requirements.txt
python -m pip install --no-deps -e .
python -m pytest -q -rs tests research/probes
python -m pip freeze > environment.txt
git rev-parse HEAD > commit.txt
uname -a > host.txt
lscpu >> host.txt
free -h >> host.txt
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python benchmark.py --repetitions 30 > benchmark-run-1.json
python benchmark.py --repetitions 30 > benchmark-run-2.json
python benchmark.py --repetitions 30 > benchmark-run-3.json
```

Keep all raw samples and peak RSS observations; report median, p95 and paired
overhead for each workload separately. Check semantic equality before timing.
Record host conditions and variation across runs. Do not select only the fastest
run. No performance threshold is justified until baselines are reviewed.

## Release gate

- Required checks pass for the exact candidate head and integrated main.
- Review compatibility, public API, limitations, changelog and user examples.
- Review the runtime, dynamic and build inventories, notices, artifact contents
  and redistribution obligations; automated audit is not legal approval.
- Record controlled benchmark results on an authorized dedicated host.
- Explicit owner decision on version, name availability and publishing.
- No upload, tag or publication as part of validation.

Optional local dynamic execution uses one classical register and limited
feedforward; it is not a hardware, arbitrary-control-flow or noise SDK.
Advanced algorithms outside the documented reference examples are future work,
not required to close the bounded pre-alpha engineering scope.

For verification engineering, additionally run `python research/public_defect_cases.py`, `python research/verification_scaling.py --repetitions 30` and, in the separately audited QCEC environment, `python research/verification_scaling.py --external --repetitions 30`. Capture artifacts and raw timing/RSS data. Different verification guarantees must not be used as interchangeable speed comparisons.

## Pre-alpha stabilization

The installed-wheel smoke now covers the complete phase-diagnosis and evidence reproduction workflow, plus a separate clean wheel installation with the dynamic extra. Stub signature parity is checked against runtime callables. Diagnostic timing includes fluent construction and dense/streamed variance with matched outputs. A separate authorized dedicated host is still required before public distribution; CI results do not satisfy that condition.
