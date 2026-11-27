# Contract lab — research qualification roadmap

No public API or runtime changes. No release authorization. Python is the
developer-facing interface, Rust the bounded exact kernel. All scopes explicit.

## Workstreams
| ID | Workstream | Gate |
|---|---|---|
| Q01 | Mathematical coverage | independent dense/symbolic oracle; valid and mutant cases; exact vs approximate scope |
| Q02 | Contract forms | identical reports for masks, labels, named wires and fluent forms; independent human comparison |
| Q03 | Native planner | batch and exact cone/factorization in Rust; aggregate budget including witness |
| Q04 | Algorithms | structured and held-out entangling workloads, coherent action, noise and transformation scopes |
| Q05 | Performance | matched cold/warm reports, raw samples p50/p95, throughput; controlled host #100 |
| Q06 | Memory | isolated processes and allocation peaks, explicit bounds, stress |
| Q07 | Packaging | locked cross-platform wheels, clean installation, portable tags, reproducibility |
| Q08 | Security | RustSec, inventory, third-party notices, input and dependency review |
| Q09 | Developer study | independent packet review #462 and consenting participants #165 |
| Q10 | Integration | reviewed exact-head CI, compatibility and owner scope approval |

## Run the actual lab
From the checked-out research branch, Python 3.12, Rust and pip:
```sh
python -m pip install -c constraints/linux-py312.txt -r requirements.txt
python -m pip install --no-deps -e .
python -m pip install maturin==1.9.6
cd research/native_contract_engine/pyo3
python -m maturin build --release --locked --interpreter python --compatibility off --out ../../../lab-wheels
cd ../../..
python -m pip install --no-deps lab-wheels/*.whl
python research/native_contract_engine/contract_lab11.py --repetitions 30
python research/native_contract_engine/contract_lab11.py --repetitions 30 --json > lab.json
```
Use the correct single wheel for your OS; the example is Linux-shell oriented.
The JSON contains raw timings and actual reports; do not synthesize timings.
Forms are experimental, not public API. Labels are highest wire first;
wire products reject duplicates instead of silently composing noncommuting
operators. Separate clean-subspace spec from transition. Reuse a frozen
LabSession explicitly. No claim of human usability from automated parity.
Existing public snapshot Contract remains unchanged.

## Review cycle
For each workstream, require scoped semantic equality before timing; inspect
failures before promoting, record regressions and rejected optimizations;
rerun exact head; retain raw data. Do not close #100/#165/#462 without their
external evidence. Shared CI cannot qualify dedicated host. No implicit
fallback, no automatic merge or publication.
