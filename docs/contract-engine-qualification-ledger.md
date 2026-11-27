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
