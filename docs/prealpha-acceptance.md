# Pre-alpha acceptance (PA02–PA05)

Scope freeze: no additional algorithms, public features or backend integrations.
The candidate stays 0.1.0.dev0; no tag or package upload.

| Gate | Evidence | Outstanding |
|---|---|---|
| PA02 API | runtime/stub signature parity, mode/compatibility regression tests, guides | owner acceptance; richer mode types future work |
| PA03 onboarding | five-minute example, mathematical/verification guides, known limitations, installed-wheel smoke | independent developer feedback (PA06) |
| PA04 benchmark | equivalent-workload fluent and variance timings, existing scaling and RSS scripts | controlled authorized dedicated host |
| PA05 distribution | wheel/sdist metadata/member checks, clean core and dynamic install, dependency inventories and scans | human license/name/trademark review and release decision |

Exact defaults and runtime semantics remain authoritative; stubs check
argument shape, not full dependent types or correctness. No independent
reviewer approval or scientific superiority is asserted. Check the CI for
the exact head; this document is not a passing test report.

To inspect and reproduce: see [release validation](release-validation.md),
[third-party review](third-party-review.md), [getting started](getting-started.md).
