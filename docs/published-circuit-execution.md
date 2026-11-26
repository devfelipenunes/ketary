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
