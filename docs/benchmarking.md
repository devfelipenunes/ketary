# Reproducing the L0 benchmark

Use a dedicated Linux machine and Python 3.12. Record CPU model, RAM,
OS, Python patch, commit, power policy, background load, and thermal state.
The validation constraints are the observed CI resolution, not a hash lock
or a promise of cross-platform equivalence.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -c constraints/linux-py312.txt -r requirements.txt
python -m pip install --no-deps -e .
python -m pip check
python -m pip freeze > environment.txt
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GITHUB_SHA="$(git rev-parse HEAD)"
# Choose a CPU allowed by the current process affinity.
taskset -c 2 python benchmark.py --repetitions 30 > benchmark-results.json
```

CPU 2 is an example; choose an available dedicated CPU. Repeat at least
three times, retain every run and report medians/p95 and absolute deltas.
Use equivalent outputs and report the extra work done by validated snapshots.
Retain the historical workload, add mixed gates including bound rotations,
and measure composition scaling. Process RSS remains a separate 20-qubit
scenario. No strict noisy CI timing threshold; investigate regressions against
the prior provisional targets. Shared CI results are diagnostics, not
controlled-hardware evidence. A dedicated-machine run is still required.
