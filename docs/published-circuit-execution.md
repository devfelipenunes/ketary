# Published circuit execution study

Exploratory sample of 16 public QASMBench files at commit
357b942396d5c2b7cbc1c229c585a6ef5ccaebac. Each original file is fetched only
for this study or read from a user-provided checkout and verified against its
Git blob SHA-1. No external code or raw circuit source is redistributed.
See [upstream license](https://github.com/pnnl/QASMBench/blob/357b942396d5c2b7cbc1c229c585a6ef5ccaebac/LICENSE)
and [paper](https://doi.org/10.1145/3550488).

The measurement is explicitly an ideal unitary projection, not execution
of the whole measured program. Remove barriers and terminal measurements;
exclude mid-circuit readout, classical/dynamic operations and unsupported
parser inputs. Preserve gate ordering and global phase. Native Qiskit
parses the original and provides the independent numerical reference.
Test strict direct import first; where rejected, identify the separate
native basis translation to u/cx. No unsupported gate acceptance is implied.

Four state inputs per accepted circuit, including a deterministic complex
state, with maximum component error <=1e-9; full complex operator comparison
for <=6 qubits. Larger widths are selected-state evidence only. Report
every excluded/error case and both import paths. No hardware execution,
shot equivalence, complete dynamic support, independent backend validation,
or human usability claim. The CI workflow is triggered only by changes
to the study and manual dispatch, so routine SDK CI does not depend on
availability of upstream files. The ordinary tests use authored fixtures.

Reproduce:
```sh
python research/published_circuit_execution.py --fetch-public
# Or point at locally checked-out files; every file hash is verified.
python research/published_circuit_execution.py --root /path/to/QASMBench
```

Candidate study; report results after both the study workflow and normal
validation pass. No publication or separate dependency is introduced.

## First observed results (pinned corpus CI)

[Run 45759569273](https://github.com/devfelipenunes/ketary/actions/runs/45759569273),
head 74e95a42, passed. Of 16 original sources, 11 unitary projections
matched complete operators and four state probes; one (10-wire Ising)
matched four selected states only. Nine accepted direct imports and three
required explicit native basis translation (QAOA n6, QFT n4, W n3).
Three excluded (BB84 n8, QAOA n3, QEC SM n5: operation after measurement),
one parser rejection (VQE UCCSD n4: undefined q at line 225), zero numerical
mismatches and zero execution errors. Largest measured operator component
error 1.85e-15, largest state component error 1.66e-15 (rounded upward).
This is coverage of a scoped ideal projection, not 16/16 full-circuit
support or independent verification of Qiskit itself.

The matched writing study in #48 returned 8/8 operator matches but
254 native versus 404 Ketary tokens: no general concision advantage.
The rotation layer was shorter (33 to 22), repeat tied (31), and native
ansatz factories were substantially shorter. Next prioritize compact
pair placement, parameterized composition, and grouped measurement before
claiming an expressive advantage. Preserve results even when unfavorable.
