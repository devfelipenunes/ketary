# Third-party dependency review (experimental)

Ketary's own code is Apache-2.0. The wheel is intended to contain only Ketary
and its distribution metadata, not vendored runtime libraries or binary
dependencies. Pip resolves dependencies separately. Do not remove their
licenses or notices. Bundling another distribution, container, or native
library would require a separate review.

Observed validation inventory: CI run 45738240604, Python 3.12, Linux.
Metadata declarations, not a legal conclusion.

| Runtime distribution | Observed version | Declared license / review |
|---|---|---|
| Qiskit | 2.6.2 | Apache-2.0 |
| NumPy | 2.5.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0; bundled notices require inspection |
| SciPy | 1.18.1 | BSD declaration; full bundled notices and binary components require inspection |
| rustworkx | 0.18.1 | Apache-2.0 |
| dill | 0.4.1 | BSD-3-Clause |
| stevedore | 5.10.0 | Apache-2.0 |
| typing-extensions | 4.16.0 | PSF-2.0 |

Development tooling includes coverage (Apache-2.0), mypy (MIT),
pathspec (MPL-2.0 declared classifier), pytest (MIT), and transitives.
These are not vendored into the runtime wheel. Check the generated graph
rather than treating this table as exhaustive for every environment.

Upstream references:
- https://github.com/Qiskit/qiskit/blob/main/LICENSE.txt
- https://numpy.org/doc/stable/license.html
- https://github.com/scipy/scipy/blob/main/LICENSE.txt

CI records runtime, validation and build dependency metadata separately,
including hashes of discovered installed notice files. It scans exact
resolved validation versions using pip-audit. Build inventory is separate; current packaging CI also scans resolved build
tooling. A hash-pinned transitive toolchain remains open.
Artifact manifests verify membership and SHA-256, not signatures or an SBOM
certification. Absence of a known advisory is not proof of security.

Before a public release: review actual distributed files and license texts,
verify rights to any contributed material, review bundled binary notices if
redistributing dependencies, verify project name availability and trademark
risk, and obtain explicit owner approval. The attempted PyPI name lookup
was inconclusive; do not infer availability. No upload or reservation.

## Dynamic extra

The optional `qiskit-aer==0.18.4` distribution is installed separately, not vendored. The dynamic CI job generates a dedicated dependency and license inventory and scans resolved versions. Its successful vulnerability scan does not replace manual review of upstream license texts, notices and redistribution obligations. The pure-state package keeps the original runtime dependency boundary. No legal clearance or publishing approval is implied.

## External verifier experiment

MQT QCEC 3.12.0 is installed only in isolated validation, not a required or bundled distribution. CI inventories its dependencies and scans resolved versions. Review upstream licensing and notices before distributing an external-verifier extra or bundled binary. See https://github.com/munich-quantum-toolkit/qcec and https://mqt.readthedocs.io/projects/qcec/en/stable/. The current experimental adapter uses an explicitly installed library. Automated metadata and vulnerability reports are not legal clearance.

### Validation tooling review

The successful CI run 45747031061 recorded Qiskit Aer 0.18.4 (Apache 2.0 metadata), MQT Core and QCEC 3.12.0 (MIT metadata), build 1.6.1 (MIT), setuptools 84.2.1 (MIT), twine 7.0.0 (Apache-2.0), wheel 0.48.0 (MIT). Workflow action revisions and these direct build/audit tools are pinned to observed successful versions; resolved build dependencies now have a separate vulnerability scan. This is not a complete hash-locked transitive environment, nor a legal approval of redistribution. Upstream notices remain required when bundling third-party distributions.

Pre-alpha artifact validation additionally checks metadata (name, version, Python requirement, SPDX license and extras), duplicate/path traversal entries, archive member types, clean wheel installation with and without the dynamic extra, and source install. These checks do not establish trademark clearance, name reservation or legal approval. PyPI name availability remains unconfirmed; recheck the official index immediately before any authorized release. No upload or reservation.
