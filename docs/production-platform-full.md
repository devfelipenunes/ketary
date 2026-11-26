# Full candidate platform qualification (PROD27)

The additional on-demand/qualification-PR workflow attempts the same Core and
Dynamic pytest scopes as the Linux gate, plus strict typing and branch coverage,
on Linux, Windows and macOS under Python 3.12. It builds wheel and sdist and
installs each in a fresh cross-platform venv outside the repository, including
the dynamic wheel extra. No uploads to a package index. Resolved dependency
versions and test JUnit/coverage reports are recorded per OS; Linux constraints
are not assumed to be cross-platform locks.

The existing smoke workflow and Linux dependency/external verifier, packaging
and benchmark workflows remain unchanged. Full candidate platform qualification
is intentionally path-scoped/on-demand to avoid tripling every development
cycle; rerun against the exact release candidate before claiming portability.
Failures/skips are evidence, not support claims. QCEC is a separate Linux
optional qualification, not implied for Windows/macOS. Reproducible dependency
locks, per-platform security/license review and independent user acceptance
remain separate gates. 
