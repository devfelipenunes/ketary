# Alpha candidate readiness (internal)

Target 0.1.0a1, not a release authorization. Current metadata stays
0.1.0.dev0 until exact qualification and owner approval.

## Evidence ledger

| Gate | Evidence required | Status |
|---|---|---|
| Integrated tree | candidate-head CI, merge-tree comparison, main push CI | pending final |
| Core and Dynamic | required tests, 95% coverage floor, warnings/skips reviewed | pending final |
| Native interop | exact full operator, selected-input distinctions, supported capability matrix | pending |
| User workflows | VQE, QAOA, evolution, defect replay; runnable instructions | pending |
| Artifacts | wheel/sdist, isolated core/dynamic/source install, archive manifest | pending final |
| Dependencies | pinned environment, runtime/dynamic/build/external inventories, audit results, manual notice review | pending |
| Performance | matched outputs, raw p50/p95 and isolated RSS, authorized dedicated Linux host | pending host |
| Usability | 3–5 external Python/quantum developers, frozen task packet | pending participants |
| Scope | known limitations, compatibility, API lifecycle, changelog, owner decision | pending |

## External formative study

Give each participant a clean Python 3.12 environment, neutral docs and
matched Qiskit and Ketary versions; alternate route order, record previous
Python/Qiskit experience separately. Three tasks with independently frozen
criteria: variational optimization, relative-phase bug diagnosis, and
modifying a Hamiltonian workflow. Use equivalent tasks with different
coefficients/parameters to mitigate carryover. No source from the calibration
suite in the instructions. Capture completion time, correctness, help
requests, defects and maintenance changes. Record failures and withdrawals;
small sample is formative, not a population estimate. Consent and anonymized
records required; no contact data in the repo. Agent assessment separate.
No claims until actual sessions and independent review.

## Dedicated host and packaging

Follow docs/release-validation.md; record commit, CPU, RAM, affinity,
environment, raw replicates, output equality. Shared CI does not satisfy
the host gate. Inspect distributions and third-party notices; manual
review is not replaced by vulnerability scanning. No tag/upload/publish.

## Integrated baseline 7e973206

PR #482 qualified head 9a7771a356c291a3e8deb40c82f2a93ce2cccfe5, 20/20
workflows, six SDK jobs, 4909 Core and 4999 Dynamic tests passed; coverage
96.977975% and 97.029196%. Merge tree 7e97320609393e7dcca163f71217bd44b4a45049
matched the candidate. Main push CI was not separately observed. This is
historical evidence, not qualification of a later commit or release.

[Parallel issue ledger](alpha-parallel-issue-ledger.md) separates the active
engineering packages and external gates. Use the counterbalanced
[formative packet](alpha-study-packet.md); independent freeze and recruitment
remain pending. Check built archive identity and layout with
`python -m research.alpha_distribution_audit <wheel> <sdist>`; the checker
is not an install, reproducible build or legal approval. Run clean wheel and
source installs using the existing CI. Dedicated-host protocol remains
[release validation](release-validation.md); do not execute it on an
unauthorized or shared host and call the result controlled evidence.
