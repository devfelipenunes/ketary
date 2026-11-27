# QContract — Consolidation and performance roadmap (provisional name)

This document names the research initiative only. Repository/package/public
API names remain unchanged pending an explicit migration and namespace review.
Goal: a usable quantum specification and verification framework, adopting
well-established techniques rather than claiming novelty for their existence.

## Acceptance criteria

- Correctness before performance: independently checked exact outputs;
  numerical and exact results labeled separately; no speed comparison on
  unresolved obligations as though they were successful.
- Matched workloads and scopes; pin competitor versions, record seeds, gates,
  width, non-Clifford content, environment, setup, query and report overhead.
- Compare optimized competitor APIs, not only scalar loops.
- Distinguish cold end-to-end costs, prepared query costs, native-format and
  normalized-output costs. Record median, P95, raw samples and coverage.
- Prefer measured wins on a scoped domain; a loss is useful evidence too.
  Shared CI is screening, not a controlled benchmark or speed release gate.

| Epic | Deliverable | R32 status |
|---|---|---|
| C01 inventory | Map current research branches and 50 gate evidence to candidate | Existing ledger, update pending |
| C02 integration | Single maintained implementation with preserved legacy semantics | Batched facade dispatch submitted |
| C03 architecture | Explicit backend capabilities, selection and resource policy | Lookup opt-in; no automatic adoption |
| C04 semantics | Exact domain matrix and independent oracles | R31 domains passed; R32 parity submitted |
| C05 API | Usable immutable prepared API with predictable results | Private API only; public review pending |
| C06 algorithms | Representative full algorithms and mutant corpus | Earlier suites; broaden matched corpus |
| C07 performance | Best available Qiskit, Stim, QCEC baselines; fair comparison | Four R32 jobs submitted |
| C08 security | Strict FFI, bounded work, notice and vulnerability review | Packed admission submitted; audit pending |
| C09 distribution | Portable wheels and reproducible builds | R31 all three hosts identical locally; R32 candidate pending |
| C10 documentation | Installation, runnable examples and exact guarantees | Pending consolidated API |
| C11 science | Related work, reproduction, limitations, external review | Research references below, dedicated study pending |
| C12 alpha | Integrated tested artifact and compatibility decision | Pending merge/API approval |

## Technique adoption

- Qiskit PauliList vectorized Heisenberg evolution and Rust-accelerated
  Pauli propagation: compare vectorized baseline, not only per-Pauli loop.
  https://github.com/Qiskit/pauli-prop
  https://github.com/Qiskit/qiskit/blob/main/qiskit/quantum_info/operators/symplectic/pauli_list.py
- Stim inverse tableau and bit-packed stabilizer arithmetic:
  https://github.com/quantumlib/Stim
- MQT QCEC portfolio of decision diagrams, simulation and ZX rewriting:
  https://mqt.readthedocs.io/projects/qcec/en/stable/equivalence_checking.html
  https://github.com/munich-quantum-toolkit/qcec

These are external references and benchmark dependencies, not code copied
into the SDK. Evaluate licenses and scope before any integration. Pauli-prop
near-Clifford comparison is a follow-up; Qiskit dense expectations and
vectorized Clifford evolution are the R32 actual comparison paths.
QCEC full-unitary equivalence is not a substitute for individual contract
semantics. Consider ZX simplification only with independently verified
rewrites. No generic superiority or scientific novelty claim.

## R32 implementation and workload matrix

- Four-bit grouped ordered Pauli products in a persistent inverse tableau,
  optional lookup class. Up to 32 groups of 16 rows; trade memory and setup
  against dense-query speed. Packed 17-byte little-endian records reduce
  Python object allocation. Strict exact bytes, widths, signs and budgets.
- R30/R31 facade coalesces exact transitions only when each per-obligation
  slice can cover worst-case tableau query plus compact witness. Preserve
  independent budget exhaustion otherwise. No default lookup adoption.
- Exact suite: 12 partial/full widths, 128 images each, independent oracle,
  packed and tuple parity, mixed budgets and full facade report parity.
- Clifford: 4/16/32/64 wires, 256/4096 gates, sparse/dense observables,
  batches 1/64/1024, 48 cases, separate setup, tuple, packed output,
  Qiskit vectorized native output and normalized bytes, Stim loop.
  Full typed report batching vs individual reports at batch 64.
- State: 4/8/12/16/20 wires, GHZ and random brickwork, 8 observables each;
  native exact Heisenberg expectation and report against numerical Qiskit
  Statevector, prepared and end-to-end; track decisive coverage.
- Equivalence: 4/8/16/32 wires, Clifford and Clifford+T, equivalent and
  mutant pairs. QCEC and native full report; Qiskit Operator at <=8 wires.
- All R32 suites pending exact-head CI. No benchmark speed conclusions yet.

## Verified R31 baseline

Head 790463a492b1245bd1eb8598a57a7144389b6575, R31 run 46056380359:
4/4 jobs passed. Domain artifact records 192 checks. Three original
platform artifacts (Linux x86_64, Windows AMD64, macOS arm64) report
same-host byte-identical wheels and zero differing wheel members.
Windows /Brepro experiment resolved the R30 discrepancy on that runner.
Notices inventory has one missing local notice entry per platform:
editable project distribution ketary 0.1.0.dev0 (own project LICENSE
exists in source; installed distribution metadata issue still open).
No cross-host reproduction or legal clearance. R30 historical cancelled
workflow remains, so 29/30 returned exact-head workflows passed.


## Integration candidate — Alpha A1

R32 exact head dd3c40ff9f0d7588e92e199409003c62244f468f completed
31/32 workflows; historical R30 cancellation only. Four R32 jobs passed:
5384 exact, 17424 Clifford, 80 state, 16 equivalence checks = 22904.
Original artifact IDs 15227508026, 15227960621, 15227253246, 15226789582
were inspected. Lookup tuple beat baseline tableau tuple in 11/48 cases
(median ratio baseline/lookup 0.854); keep conventional default.
Packed lookup beat Qiskit vectorized normalized output in 48/48 cases
and Stim loop in 48/48, with median scenario ratios 385.26 and 22.94.
These compare prepared representations on shared CI, not generic SDK
execution. At 64 wires/4096 gates/dense/1024: packed lookup 0.111274 ms,
tableau tuple 0.281375, Stim loop 2.582382, Qiskit normalized 23.753357.
Snapshot export from SDK median 5.454844 ms in this case.
Batched full typed reports beat per-item reports in 16/16 scenarios
(median speedup 1.4682). Retain safe batching. Do not auto-select lookup.
All 80 exact state expectations agreed with dense reference; some small
prepared dense queries were faster. All 16 equivalence pairs agreed with
QCEC; simple appended-inverse and mutant fixtures only, unequal setup
boundaries, not a general verification advantage.

C01 inventory: exact R32 is 131 commits ahead of main 084418d6 and zero
behind, 155 changed files; 16 stacked open PRs #512–527. Candidate
integration branch preserves them, without merging/closing them.
C02/C03: explicit 32-module runtime dependency closure with generated
relative imports; extract selected declarations from benchmark-heavy
modules, preserve original research. Runtime manifest binds source and
generated hashes. No benchmark ctypes loaders or executable suites in
wheel. This is a transitional packaging boundary, not final module
refactoring or independent source review.
C04/C05: provisional qcontract API, direct canonical Qiskit snapshot,
explicit contracts/statuses, domain/snapshot binding, selected replay,
immutable diagnostics. Existing legacy package unchanged in repository.
C06: isolated tests of all ten families, GHZ up to 64 wires,
Bernstein-Vazirani, mutation and exact negative controls.
C07: R32 comparative evidence above. Dedicated controlled benchmarks
and matched Pauli-prop comparison remain open.
C08/C09: candidate wheel manifest/contents audit, native RECORD audit,
fresh venv and pip check; CI on Linux/Windows/macOS. Private native wheel
still uses historical distribution/import name; local Python distribution
qcontract-alpha-local and import qcontract are provisional. No registry
upload, final package namespace, portable platform tags or legal clearance.
C10: docs/qcontract-alpha-guide.md describes local installation and
exact domain boundaries. C11: related work and external protocols remain
in ledger; independent reviewer, hardware and participants still needed.
C12: one integration PR targeting main, exact-head build and regression
required before review/merge. No merge, publication or branch deletion.
Alpha A1 CI results pending.


## Alpha A2 — packaging identity, replay and reproducibility

A1 exact head 4c9f5523f9fb22843a50529cfbe29c9cb39f0aa5: 32/33
workflows succeeded (historical R30 cancellation only). Qualification run
46062634678: 3/3 platform jobs passed. Original artifacts
15229094725 (Linux), 15229566740 (Windows), 15229009408 (macOS) audited:
41 checks per platform, 123 executions of the installation checks;
32 runtime modules, 40 wheel members; clean virtual environments without
the legacy SDK. CPython 3.12 and Qiskit 2.6.2. All wheel SHA-256 values
match the qualification metadata at source commit. Linux and macOS pure
Python wheel digest 77e7d0b8d37a903766906b38d3651ed87494298f7fbb51ee612592af4e9c06d2;
Windows digest fac2fe0d22b567f1ff16c008618f5a7624c68d50f2edb907991c92c554b147c7.
Member comparison: Python sources, README metadata and license differ
only by CRLF; manifest and RECORD hashes differ; ZIP host/permissions
metadata differ. Native wheels have platform-specific tags and digests,
not expected to match across architectures.

A2 action:
- C02/C09: isolated staged native crate substitutes only local distribution
  and module namespace (qcontract-native-alpha-local / qcontract_native_alpha);
  preserves the research crate and dependency versions. Record hashes of
  original canonical source and staged native files. Local Python
  distribution remains qcontract-alpha-local, version 0.1.0a1. No PyPI
  registration or permanent namespace allocation.
- C08/C09: normalize text to LF, pin setuptools 80.9.0 and wheel 0.45.1,
  canonicalize pure-Python ZIP container metadata only (fixed timestamp,
  order, permissions and stored entries); assert every member is unchanged
  and verify RECORD. Compare cross-platform digests after CI; do not claim
  equality before results. Native binaries never post-processed.
- C04/C05/C08: independent Python ordered-Pauli replay for tableau reports.
  Verify PASS equality and FAIL product-state witness value, masks, axes,
  signs and snapshot/obligation binding. Replay returns None on insufficient
  logical budget. Selected existing state/certificate routes unchanged.
- C06: installed candidate tests include PASS/FAIL replay, tampering,
  low budget and absence of legacy native distribution/module.
- C07: preserve existing performance defaults and evidence; no new speed
  claim. C10: update guide to reflect staged native name and replay scope.

A2 pending exact-head CI. Review portable Linux tags, source admission
hardening, stable public types, external review and dedicated benchmarks
before Alpha release. No merge, public upload or deletion of historical PRs.


## Alpha A3 — SDK usability and end-to-end performance

A2 head 00b53ac6b92e921c7a100eda71af0ada64ee25c6: 32/33 workflows
succeeded (historical R30 cancellation only); run 46067956376 all three
platform jobs passed. Original artifact IDs 15232415337, 15232293625,
15231628742 audited; 48 checks per platform (144 executions), 32 runtime
modules, 40 wheel entries, native distribution and import renamed.
All wheel hashes agree with qualification metadata. Linux and macOS
pure Python wheel SHA-256 e2cafac689336238ea0eb69ed3e3ee6a27ae8b7f12d696c4ae1f3fdc698daf7b;
Windows e2111f206c37e84fe26bbfe727b8481711c7cfea90133eb869c1cc587ca2320b.
Only METADATA (CRLF vs LF) and its RECORD row differed; all executable
source and other members matched. A3 normalizes that metadata only
and regenerates RECORD, audits original and final RECORD, and asserts
all other members are unchanged. Cross-platform equality pending A3.

C05/C10: public typed stub, PEP 561 marker, runtime specification union,
positive and negative installed mypy checks, guide and API version
0.1.0a2. C08: canonical concrete gate admission; reject spoofed base_class
and altered mutable gate definitions; negative controls for spoof/open
control and positive canonical mutable control. Not a Python sandbox.
C06/C07: installed API benchmark across 4/16/32/64 wires, 256/4096 gates,
sparse/dense observables, batches 1/64 (32 scenarios; 1040 verdict
comparisons per platform). Matched Boolean verdicts, separate full
reports, preparation, end-to-end and P95/raw samples. QContract computes
more diagnostic data; no speed claims before results.
C09: A2 qualified installation, metadata reproduction correction
pending. C11/C12: no external study, controlled benchmark, registry
upload, public release, merge or historical PR deletion. A3 CI pending.


## Alpha A4 — isolated dispatch optimization candidate

A3 head a44c82647331d2ad6f85c7f3597eb6ec99db2c4b remains unchanged
on integration/qcontract-alpha and PR #528. At the start of A4 all
33 A3 workflows were queued (run 46077884300 for isolated wheels).
Do not invalidate the pending A3 evidence by pushing this experiment
into its branch prematurely. A4 branch integration/qcontract-alpha-a4
is based on that exact head and is not yet a release candidate.

Code inspection identified repeated validation, obligation hashing,
legacy object creation and nested report allocation in pure base
requests. These are hypotheses, not measured bottleneck shares.
R31 adapter delegates base-only requests once. R30 adapter has a
specialized path only for validated all-transition batches with an
available prepared Clifford tableau. Native compact witness/verdict
results become the same typed reports and attempt metadata directly.
The exact native logical charge per item is
1 + popcount(post.x) + popcount(post.z) + 2*(2*width+3).
Preflight all items, admit only those whose individual equal quota
covers this charge, batch only admitted entries, and preserve original
order, snapshot, obligation IDs, witness, route and reservations.
No shared-budget borrowing, no mathematical kernel change, no cached
verdict, no new public API. Mixed, non-Clifford or unprepared requests
retain existing routing.

Installed dispatch_parity.py compares complete raw reports against
reconstructed A3 pure-transition dispatch, plus independent Qiskit
signed Clifford results. Twelve widths (including partial mask widths
and 64), batch sizes 1/2/7/64, exact cost thresholds, sparse/dense
inputs, PASS/FAIL, low budget, invalid input, mixed domains and
fallback controls. Twenty-four paired dispatch timing scenarios.
This reference is for regression parity, not independent proof.
A3 actual public API benchmarks and A4 same-host dispatch experiment
must be read separately. No speedup claim before measured results.

A4 validation hook is implemented but not invoked by A3. Hold branch
integration until A3 exact-head CI results are inspected. No merge,
release, branch deletion or public package/version change.


### A3/A4 offline verification while CI queued

Revalidated original A2 artifact ZIPs (IDs 15232415337, 15232293625,
15231628742), both wheel digests against their qualification metadata
and every pure-Python RECORD row. Applied the A3 metadata normalization
and deterministic ZIP algorithm locally to the original wheels without
modifying them. Windows METADATA had 107 CRLF endings; Linux/macOS zero.
All three normalized wheels (40 members) have SHA-256
d6d33ea8e222fc3547d993db71bd3a114c427c09440d6d17942661689c757fa2.
Second normalization produced byte-identical output for each archive.
This is a regression check on existing A2 artifacts, not evidence of
new A3 compilation or portable native binaries. Added a reusable
verify_wheel_normalization.py offline tool that checks RECORD,
normalization, idempotence and equality without mutating inputs.

For A4, reconstructed the actual modified qualified30/31 sources
from the A2 installed Python modules plus the exact A4 changes;
verified Git blob SHA-1s 514f198a917c416d5e01994ea8c7ed3727b7ebd4 and
dc01fa771dbfe03a994f5825de25b8725cec7b98 before executing them.
Compared complete old/new Python report fields via dataclasses.asdict,
with a mock native tableau using independent_image and the exact
compact-witness arithmetic. 7,918 report comparisons in 428 scenarios
passed (12 widths, four batch sizes, varied per-item budget boundaries,
24-gate seeded Clifford inputs, positive and negative obligations).
This is a local dispatch regression, not real FFI or Qiskit parity,
not an installed-wheel test, and not performance evidence. The local
environment is Python 3.13/glibc 2.41, lacks Qiskit and Rust tools;
the A2 native wheel requires CPython 3.12 and was built on glibc 2.43.
A3 and A4 native qualification remain required. No release or merge.


### A4 distribution portability qualification

Audited original Linux A2 wheel from artifact 15232293625 using readelf
on its actual ELF x86-64 extension. The runner had glibc 2.43; the
maximum required GLIBC symbol version is 2.34, not 2.43. DT_NEEDED:
libgcc_s.so.1, libc.so.6, ld-linux-x86-64.so.2. Highest GCC symbol
version is GCC_4.2.0. This is static binary evidence, not a guarantee
of runtime or dependency compatibility. A2 still carries linux_x86_64
rather than an audited manylinux tag.

A4 changes only the candidate qualification: build Linux with Maturin
--compatibility manylinux_2_34, assert the audited tag, inspect required
ELF versions with readelf (reject unknown GLIBC versions and requirements
above 2.34), and retain the original RECORD and isolated-install checks.
Use the existing Linux job on ubuntu-22.04 rather than adding jobs.
This exercises glibc 2.35, not the exact 2.34 floor. An older-host
2.34 runtime test, ARM64 Linux, Intel macOS and additional Python versions
remain outside the validated matrix. Shared-host benchmark medians
cannot be directly compared between different runner images; A4 paired
dispatch reference uses the same host.

References: https://www.maturin.rs/distribution and
https://docs.github.com/en/actions/reference/runners/github-hosted-runners.
A3 head and workflows are unchanged. A4 remains auxiliary and unvalidated
with the real native extension. No manual binary relabeling, no upload.
