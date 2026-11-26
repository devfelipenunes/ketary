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
