# QContract application portfolio

Ten bounded ideal-circuit applications exercise the existing Alpha.
Together with the separate finite-error code audit (#549), the portfolio
targets all ten existing contract families without adding a predicate.
The earlier Bernstein–Vazirani and non-Clifford project examples remain
available; this portfolio is not a new methodology expansion.

| Application | Decision | Contract families | Fixtures |
|---|---|---|---:|
| GHZ distribution | Accept a three-party entangled resource | StateEigen | 4 |
| Cluster resource | Detect graph edge or phase defects | StateEigen | 3 |
| Dense coding | Verify each of four decoded messages | StateEigen | 8 |
| Bell branch audit | Verify conditional receiver moment and probability | ZBranch | 4 |
| Partition audit | Detect unintended coupling of two Bell resources | Separable | 2 |
| Coherent teleportation | Verify logical state transfer with clean initial workspace | RelativeAction | 4 |
| Parity workspace | Check uncomputation and coherent logical parity phase | CleanInput, RelativeAction | 4 |
| Compiler rewrite | Distinguish exact, phase-equivalent and incorrect reductions | Equivalent | 3 |
| Hamiltonian mapping | Check rational observable remapping under wire permutation | SumTransition | 4 |
| Noise transfer | Check predicted attenuation under a specified finite Pauli channel | NoiseAfter | 10 |
| Finite error audit (#549, separate PR) | Select compatible repetition code, audit encoder | Correctable, Transition | 8 code/model combinations, separate encoder controls |

The ten applications in this branch have 46 fixtures. They use fixed
expected classifications, independent small Qiskit numerical references
and negative or permitted-variation controls. The separate #549
application is not imported by this runner. Its integration must be
checked independently. The numeric reference is not an exact proof.
A fixture may contain multiple obligations; fixture counts are not
unique mathematical proofs or independent developer experiments.

Run `python -I docs/qcontract/applications/run_portfolio.py` in the
qualified installed-wheel environment. The CI report
contract-application-portfolio.json contains all ten result groups.
Require successful exact-head CI, then verify the integrated main tree.

## Boundaries and feedback

These are engineering decision demonstrators and small ideal algorithm
workloads, not deployed systems. No dynamic circuits, hardware execution,
device calibration, arbitrary CPTP noise, VQE optimizer, general
compiler, fault-tolerant recovery or quantum advantage claim. Do not
weaken a requirement or broaden the engine just to make a fixture pass.
Capture actual errors, unsupported or unresolved results and API friction
when the examples execute. Change the engine only for a concrete
demonstrated need; external usability studies remain separate.

## Integrated portfolio

See [algorithm suite](algorithms.md) for fourteen additional workloads and
[engineering evaluation](evaluation.md) for the integration and scaling
controls. The 25 applications are distinct from the methodology rounds;
the new integrated candidate requires fresh qualification.
