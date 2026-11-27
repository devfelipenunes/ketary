# Contract Engine — candidate qualification ledger, R25

This ledger supplements the master roadmap; its exit criteria remain in
force. Research prototypes are not public API or release qualifications.
R24 head 91362067251ed6cacfc891ac4c75bddf72bf7a91 passed 24/24 workflows,
including all four specialist jobs. R25 is an unvalidated increment.
Status E = experimental evidence exists; T = additional R25 tests
submitted; P = pending mandatory work; B = external dependency.
A row may have both experimental evidence and pending exit conditions.

| ID | Current evidence / submission | Exit work still required |
|---|---|---|
| M01 | E: taxonomy | Independent semantics review |
| M02 | E: signed transitions and exact observable | Final integrated regression |
| M03 | E: clean subspace | Final integrated regression |
| M04 | E: equivalence modulo phase | Phase-domain separation review |
| M05 | E: logical coherent action | Independent review of input-domain semantics |
| M06 | E: monomial relative phase | Held-out adversarial coverage |
| M07 | E: sequential composition | Final integrated regression |
| M08 | E: numeric effect/CPTP | Independent numeric guard review |
| M09 | E: rational channels | Final integrated regression |
| M10 | E: rational Hermitian Pauli sums | General supported algebra limits |
| M11 | T: exact pure bipartite cut separability | Mixed-state/other domains explicitly unsupported; review |
| M12 | T: trace-nonincreasing Z branch | General feedback, CP-TNI sequential contracts |
| M13 | T: strict packed gate-induced phase | Source global-phase metadata and coherent control |
| M14 | E: arithmetic components | Final integrated regression |
| M15 | E: syndrome and recovery contracts | Extraction and mutant tests |
| M16 | T: ideal extraction and conditional recovery circuits | Noisy execution/fault tolerance outside pilot; review |
| M17 | E: exact composition of supplied bounds | Independent validation of input bounds |
| M18 | E: observable research syntax | Public API approval |
| M19 | E: private facade/prepared reports | Unified typed dispatch and compatibility review |
| M20 | E: immutable component registry | General registry/domain composition |
| M21 | E: implication and Pauli product reuse | Broader verified rule set |
| M22 | E: native compact diagnostics R24 | Diagnostics UX and failure corpus |
| M23 | T: compact binary evidence | Version migration and interop review |
| M24 | E/T: independent Clifford+T and temporal replay | Scalable independent certificates beyond local cuts |
| M25 | E: canonical snapshot | Final integrated regression |
| M26 | E: sparse exact core | Full coefficient growth and bit complexity ledger |
| M27 | E/T: bit slicing, persistent tableau, SIMD | Cross-platform parity and adoption decision |
| M28 | E: causal cones | Broader connected workloads |
| M29 | E/T: native projection, phase-weighted DAG | Direct general weighted gate execution |
| M30 | E: unified R24 routes | Full attempt trace, calibrated route ordering |
| M31 | E: disconnected and temporal cuts | General spatial factorization |
| M32 | E: logical work caps | Admission/serialization/allocator/bit-cost accounting |
| M33 | T: isolated requested allocation highwater | Dedicated process RSS and whole-extension allocation audit |
| M34 | T: explicit SSE2; prior native threads | Cross-platform validation and measured adoption |
| M35 | E/T: deterministic negative controls | Property fuzz campaigns and coverage metrics |
| M36 | E/T: algorithm corpus, numeric Ketary contracts | Larger interacting workloads and matched semantics |
| M37 | E/T: GHZ, phase, random small connected | More challenging held-out distributions |
| M38 | E: Stim/Qiskit/QCEC pilot | Controlled host, matched setup/output and competing methods |
| M39 | E: raw data with host and commit | Independent reproducibility |
| M40 | B: dedicated CPU #100 | Actual controlled host |
| M41 | E: lab and artifacts | Consolidate latest validated lab dashboard |
| M42 | E: native wheel matrix | Latest candidate cross-platform matrix |
| M43 | E: same-host byte-identical wheels | Cross-host/toolchain reproducibility and portable policy |
| M44 | E: dependency audit and inventory | Candidate SBOM, notices and security review |
| M45 | E/T: malformed FFI, SIMD audit boundary | Full admission audit and independent review |
| M46 | B: study packet #462 | Actual independent reviewer |
| M47 | B: usability #165 | Actual consenting participants |
| M48 | T: executable R25 lab examples | Complete scoped user-facing teaching material |
| M49 | P: proposed migration below | Owner approval of public API |
| M50 | P: integrated research chain | Exact candidate CI, review, mandatory gates |

## Public API ADR — proposal, not approved

Retain existing Contract snapshot semantics. Prefer a distinct prepared
verification interface only after scope and typing review. A result carries
snapshot identity, obligation identity, domain, route, budget/provenance,
and one of PASS/FAIL/INCONCLUSIVE/UNSUPPORTED. Exact and numerical evidence
must be distinguishable and cannot be implicitly promoted. Phase-insensitive
identities never certify strict source phase or controlled equivalence.
A compact witness can be expanded to its documented legacy form. Do not
automatically select experimental SIMD/threads or expose native types.
Before adoption: review type stubs, migration examples, compatibility tests,
versioned certificate readers, wheel policy, and candidate security/UX gates.
No merge, release, or public API change authorized by this document.

## Reproduce R25

From the repository root, with the private native wheel built and installed
using the same pinned dependencies as the workflow:

```sh
python research/native_contract_engine/front_master25.py binary
python research/native_contract_engine/front_master25.py weighted
python research/native_contract_engine/front_master25.py simd
python research/native_contract_engine/front_master25.py recovery
python research/native_contract_engine/front_master25.py semantics
python research/native_contract_engine/front_master25.py algorithms
rustc --edition 2021 -C opt-level=3 -C overflow-checks=yes research/native_contract_engine/profiling/alloc25.rs -o /tmp/ketary-alloc25
/tmp/ketary-alloc25
```

These commands are executable lab entrypoints, not documentation for a
released API. CI stores raw JSON, commit, environment and host metadata.
Do not treat unvalidated R25 results as completed gates.


## Qualification update — R30

R28 debeb5b3: 27/27 workflows. R29 9c1966c2: 29/29 workflows.
R29 raw exact-head artifacts: 131 FFI, 396 fallback and 7 process limit
checks (534 total). The two 64-wire T-dressed graph state obligations
were resolved PASS/FAIL by Heisenberg fallback (0.500258 ms median for
both queries, excluding preparation). Four isolated Linux workload peaks
111328–112936 KiB RSS; address-space, wall and CPU controls triggered.
These are shared-runner and fixed-workload results, not general guarantees.

| Gate | R30 action | Remaining exit requirement |
|---|---|---|
| M03–M05/M11–M13/M19 | Seven typed exact contract families, explicit domain and snapshot bindings | Validate CI, integrate channels/noise/QEC separately; source strict phase still unsupported |
| M26/M32/M33 | Opt-in native metered transition with diagnostic reserve and final coefficient bits; R29 process limits | Full bit-operation, serialization and allocator accounting; independent audit |
| M35/M37/M45 | Deterministic generated valid/invalid circuit campaign; R29 strict primitive controls | Coverage-guided fuzzing and independent review |
| M42/M43 | Linux, Windows, macOS candidate builds twice on each host; smoke tests | Validate platform jobs; cross-host reproducibility and distributable wheel policy |
| M44 | CycloneDX 1.5 candidate inventory with resolved Cargo checksums and installed Python metadata | Schema/tool verification, exact linkage scope, vulnerability and third-party notice review |
| M40/M46/M47 | Reproducible handoff protocol below | Actual dedicated host, independent reviewer and consenting users |
| M49/M50 | Preserve private interfaces; keep gate evidence separate | Explicit API approval, exact candidate qualification, merge/release decision |

### Dedicated-host protocol (M40, not executed)

Record hardware model, physical/logical core count, RAM, OS, rustc,
Python and dependency versions, CPU governor/turbo, affinity and thermal
conditions. Freeze source SHA and dependency locks. Use the same host,
workload seeds and equivalent semantics for Ketary, Stim, Qiskit and
QCEC. Separate setup, query, batch and output construction; report
decisive coverage, median/P95, raw samples and peak RSS, with randomized
interleaved order and repeated fresh processes. Preserve failures and
inconclusive cases. Do not treat shared CI as dedicated hardware.

### Independent review and usability packet (M46/M47, not executed)

Reviewer receives pinned SHA, domain taxonomy, exact oracle and native
implementation, evidence schemas, unsafe SSE2 boundary, allocation
delegation, raw artifacts and instructions to reproduce the suites.
Review phase assumptions, projection semantics, budget exhaustion,
counterexamples, parsing and FFI; record findings with reproducible
cases and severity. A reviewer must be independent of the implementation.

Recruit consenting developers; record experience level without unnecessary
personal data. Ask them to express a transition, distinguish state from
all-input contract, diagnose a false property, and interpret INCONCLUSIVE
without guidance. Measure completion, mistakes, time and qualitative
feedback. No fabricated participants or ratings; no release gate closure
until observations and remediation are recorded.

R30 remains an unvalidated private candidate increment. No merge or
release. Inventory is not a legal notice or a vulnerability-free claim.


## Qualification update — R31

R30 exact head 3dd303cf13cfbe7def441e63c43867c516de2a19: 29/30
workflows succeeded; R30 matrix 5/6 jobs succeeded, macos-14 cancelled.
A requested job retry also returned macos-14 cancelled. No macOS result
or root cause inferred. Original R30 artifacts verified against commit:
87 integrated, 1280 generated (512/512 decisive oracle queries,
768/768 invalid snapshot rejections), 576 metered = 1943 checks.
Linux and Windows platform smoke suites passed. Linux independent target
directories yielded byte-identical wheels. Windows yielded unequal
wheels: only the native .pyd and RECORD contents changed, 20 differing
overlap bytes in equal-size PE binaries (428544 bytes); observed PE
timestamps 1795806670 and 1795806684. Timestamp and other PE build
metadata are suspected contributors, not yet a proven complete cause.

| Requirement | R31 action | Remaining exit criteria |
|---|---|---|
| M09/M10/M19 | Typed rational sums and Clifford-then-Pauli-mixture contracts in shared adapter | General channels/feedback not admitted; CI and independent review |
| M15/M16 | Finite-code correctability and syndrome recovery table with explicit code/error obligation identity | Physical fault-tolerance/noisy execution not claimed |
| M32/M35 | Logical reservations and preflight tests for new domains | Admission and bigint/allocator accounting still incomplete |
| M42/M43 | Windows /Brepro experiment, alternate macos-15 runner; compare raw wheel members and PE timestamp | Successful macOS test, confirm deterministic builds, independent hosts and portable wheels |
| M44 | Collect actual local license/notice texts with SHA-256 and missing-file list | Review missing notices, exact linkage scope, vulnerability/notice/legal review |
| M49/M50 | No public API changes; private exact adapter | Final candidate integration, explicit API approval and all mandatory gates |

R31 code-set contracts use the circuit width only, not circuit identity;
they do not certify the circuit or hardware. No arbitrary CPTP map,
source-global-phase, numerical proof or fault-tolerance promotion.
The local notices inventory is evidence for review, not a release notice
or a security clearance. No external reviewer, dedicated host or usability
participant has been engaged. All R31 results pending CI.
