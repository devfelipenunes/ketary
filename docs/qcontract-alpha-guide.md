# QContract Alpha 0.1.0a3 — local candidate guide

Provisional name and API. The local distribution is qcontract-alpha-local;
the Python import is qcontract. Nothing is uploaded to a package registry.
This candidate depends on the local `qcontract-native-alpha-local` native wheel and Qiskit, not on the
previous SDK package. CPython 3.12 is the admitted interpreter.

## Install from validated local build artifacts

From a clean Python 3.12 virtual environment, install both wheels produced
by the alpha qualification workflow in a single pip command, allowing
Qiskit and NumPy dependencies to resolve. Use the exact wheels for your platform, from the same commit. The Python wheel is
`qcontract_alpha_local-0.1.0a3-py3-none-any.whl`; the native wheel is
`qcontract_native_alpha_local-0.1.0-cp312-cp312-<platform>.whl`.
Download the matching qualification archive from [run 46084014830](https://github.com/devfelipenunes/ketary/actions/runs/46084014830) and extract it. The qualified source commit is `bc16ff0b74d7766d483a5bccd7258d998826c8b3`. Compare SHA-256 against the following values and `qualification.json` before installation.

| Artifact | Native wheel filename | SHA-256 |
|---|---|---|
| Linux 15238562005 | qcontract_native_alpha_local-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl | 8a5a2cb18ca2caa4f24ee6f0376cf1351afb94fb99fb1977eae157217c0cd41f |
| Windows 15238856035 | qcontract_native_alpha_local-0.1.0-cp312-cp312-win_amd64.whl | 4315b7615f1fc09db000b8c4293e2c2f171ce92d08791920fba7844dc330f125 |
| macOS 15237893203 | qcontract_native_alpha_local-0.1.0-cp312-cp312-macosx_11_0_arm64.whl | 2fec74810ee36ae02e255f558089089b34ac0212ce42b7a8b1a7bfe9b76a0b8b |

The pure Python wheel has SHA-256 `3118ff1ad3a8ab45c87ba321a34efd667628fdb86ec992e58ddc97485273bdf4` on all three targets. From the extracted archive directory, using CPython 3.12:

Linux/macOS:
```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install qiskit==2.6.2 python/*.whl native/*.whl
python -m pip check
python -c "import qcontract; print(qcontract.__version__)"
```

Windows (PowerShell):
```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install qiskit==2.6.2 python\qcontract_alpha_local-0.1.0a3-py3-none-any.whl native\qcontract_native_alpha_local-0.1.0-cp312-cp312-win_amd64.whl
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -c "import qcontract; print(qcontract.__version__)"
```

The printed version should be 0.1.0a3. For a strict replication of dependency versions, consult the matching environment.json; the install commands above are a quickstart, not a complete dependency lock.

See [contract-first documentation](qcontract/README.md) for named plans,
examples, reference and explanations. No production compatibility or public PyPI availability is
implied.

## First exact contract

```python
from qiskit import QuantumCircuit
from qcontract import Pauli, Contract, StateEigen, prepare

c = QuantumCircuit(2)
c.h(0)
c.cx(0, 1)
p = prepare(c, prepare_state=True)

transition = Contract(requires=Pauli("IZ"), ensures=Pauli("XX"))
state = StateEigen(Pauli("XX"))
assert p.check(transition).status == "PASS"
assert p.check(state).status == "PASS"
bad = Contract(requires=Pauli("IZ"), ensures=Pauli("-XX"))
failure = p.check(bad)
assert failure.status == "FAIL"
print(failure.witness)
```

The transition proves U-dagger B U = A for all inputs. The state contract
proves that the signed Pauli stabilizes U applied to the all-zero input;
one does not imply the other. Labels use Qiskit wire order (highest wire
first); Pauli returns integer masks, so leading identity characters do
not establish a width restriction. The prepared width bounds the masks.

## Exact admitted domains

| Contract | Semantics | Current bounds |
|---|---|---|
| Contract / Transition | All-input signed Pauli identity | 1–64 wires, bounded exact routes |
| StateEigen | Zero-input signed Pauli eigenproperty | 1–64 wires, optional prepared DAG and Heisenberg fallback |
| CleanInput | Zero leakage on all clean ancilla inputs | 1–64 wires, bounded projected route |
| Prepared.action_matches | Coherent clean-input action up to phase | 1–64 wires, combined snapshot cap |
| Prepared.equivalent_to | Full admitted unitary equivalence modulo phase | 1–32 wires |
| Prepared.equivalent_to(strict=True) | Strict packed gate-induced unitary equality | 1–5 wires, <=512 gates per circuit |
| Separable | Zero-input pure state rank-one across one cut | 1–5 wires, <=512 gates |
| ZBranch | Unnormalized zero-input Z measurement branch probability/expectation | 1–5 wires, <=512 gates |
| SumTransition | Rational Hermitian Pauli sums | <=64 terms per side, bounded exact propagation |
| NoiseAfter | Clifford followed by finite Pauli mixture | <=16 weighted entries |
| Correctable | Finite error-set code criterion and recovery synthesis | Code-only; no physical fault tolerance |

Equivalence counts as one family with two explicit phase modes. All
results are scoped to the admitted gate alphabet H, S, S-dagger, X, Z,
CX, T, T-dagger. A circuit may contain at most 100000 gates; individual
routes have stricter limits (e.g. T count, terms, state nodes). Parameterized
gates, measurement/reset instructions, classical bits, arbitrary rotations
and nonzero source global phase are rejected at preparation. ZBranch
describes a hypothetical exact Z instrument on an admitted unitary
snapshot; it does not execute arbitrary measured circuits.

## Results and budgets

PASS = exact guarantee in the stated domain; FAIL = exact refutation;
INCONCLUSIVE = bounded method could not finish; UNSUPPORTED = recognized
contract outside route scope. Invalid input raises ValueError/TypeError.
Do not convert INCONCLUSIVE to FAIL or PASS. Each batch admits 1–64
contracts with disjoint logical reservations (max_work <= 2000000).
Preparation caps are separate and state preparation is opt-in. Work is
not a CPU, bit-operation, memory, or wall-time guarantee.

Prepared snapshots are immutable and isolated from later source circuit
edits. A Result includes status, domain, snapshot and obligation IDs,
reserved work, route when supplied, and optional witness/evidence/exact
expectation. Diagnostic shapes are provisional, not a stable wire schema.
Prepared.replay independently checks native Clifford transition verdicts and their exact product-state witnesses, as well as selected other transition/state routes. None means
unavailable. Evidence is not authenticated or a succinct proof of work.
Other families do not yet offer portable replay.

## Validation and limitations

The historical research remains in the repository; the staging script
selects the needed runtime declarations and uses package-relative imports.
It does not execute benchmark-only ctypes loaders. Runtime manifest hashes
bind each generated module to its original source. Native backend is a
locally staged QContract wheel, not independently security-audited. No hardware
execution, arbitrary noisy circuits, general formal verification, external
usability validation, or production readiness is claimed.


## Typed API and benchmark evidence

The local candidate 0.1.0a3 includes a PEP 561 marker and public type
stub. IDE completion and type checking cover the ten specifications,
prepared session and Result. Run the isolated qualification workflow
to see positive and deliberately invalid mypy examples. Runtime
admission remains authoritative: Python type hints are not guarantees.
Canonical Qiskit gate concrete types are required. Admission examines the
operations actually stored in the circuit; unsupported custom types, open
controls and modified mutable definitions that survive Qiskit insertion
are rejected. Qiskit may canonicalize an operation before QContract sees
it, so pre-insertion provenance cannot be recovered. Do not mutate a
circuit concurrently with preparation. This is an input boundary, not a
sandbox for untrusted Python objects.

The installed benchmark compares signed Clifford identity verdicts with
Qiskit PauliList vectorized evolution, measuring cold preparation,
prepared verdicts and full reports separately. QContract also computes
witnesses/metadata; Qiskit baseline returns Boolean verdicts only.
The comparison uses shared CI hosts, not dedicated CPU performance.

Linux candidate builds now request an audited manylinux_2_34_x86_64 tag,
with an independent ELF requirements audit and installation on Ubuntu
22.04. The exact 0.1.0a3 candidate passed isolated installation on Ubuntu 22.04 x86_64
(glibc 2.35), Windows AMD64 and macOS 15 ARM64 with CPython 3.12.
The manylinux tag is not evidence of testing every compatible host, and the
macOS wheel tag is not evidence of testing older macOS releases. Other
architectures and CPython versions are outside the qualified matrix.

`Plan`, `Named`, `Outcome`, and convenience constructors attach readable names
to existing exact obligations; they do not expand the mathematical domains.
`statuses()` omits full reports and evidence. Use `verify()` when diagnostics
or replay matter. Eligible Clifford state obligations use the same tableau route
in individual and mixed requests, with equal per-item logical budgets.
