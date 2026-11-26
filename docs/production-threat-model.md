# Production threat model and exact qualification gate

Scope: local trusted Python process, native Qiskit objects and optional native
backends; logical replay JSON is a restricted data boundary, not executable
serialization. No promise of sandboxing arbitrary Python objects, malicious
native code, QPY, user callbacks, compromised dependencies or OS accounts.
No hardware credentials, remote calls or job submission.

Threats and mitigations: malformed/oversized replay -> exact keys, duplicate
rejection, finite scalars, bounded width/instructions/bytes and allowlist;
resource exhaustion -> declared payload/work bounds before execution, not RSS
guarantees; incorrect result/provenance -> fail-closed numerical/statistical
checks, independent oracles and synthetic backend faults; mutable aliases ->
defensive snapshots and suffix rollback; optional dependency compromise ->
separate dependency/license/vulnerability review and pinned Linux resolution;
supply chain -> pinned actions, no persisted checkout credentials, wheel/sdist
install probes and exact revision evidence. No untrusted arbitrary source
execution or native deserialization. Residual risk: dependency trust, native
scratch/CPU, malicious iterables, concurrency, platform lock reproducibility,
manual upstream notices, third-party review and operational environment.

Earlier CI reports show whole-percent rounded coverage. The candidate gate
prints two decimal places and enforces 95 with six decimal reporting precision
on branch+statement combined coverage in both Linux Core and Dynamic. Do not
claim an exact >=95 before this gate passes. No existing tests removed, no
coverage exclusions or path changes. Coverage does not prove correctness.
