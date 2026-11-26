# Parallel alpha work ledger

Baseline main 7e97320609393e7dcca163f71217bd44b4a45049. The 34 open issues
are coordinated through disjoint implementation and qualification packages.
A reference below is a work association, not issue acceptance. No issue
is marked complete by a new test, candidate, or documentation alone.

| Issue | Workstream | Candidate | Remaining acceptance |
|---|---|---|---|
| #97 | binding | #468 | dense regression and exact-head benchmark |
| #190 | architecture | #483 | JSON export boundary; remaining builder/kernel audit |
| #310 | memory | #484 | exact top-k and fresh-process RSS; host pending |
| #180 | QPE | #485 | direct inverse QFT profile; decide runtime |
| #303 | parity | #484/#486 | retain existing parity baseline; evaluate shared parity and phase in new application corpus; distinct depth/RSS profile remains |
| #52 | benchmark | #468/#484/#485/#487 | raw matched profiles and controlled host gate |
| #109 | verification performance | #487 | separate verdict scopes; QCEC comparison remains |
| #90 | math differential | #486/#487 | full operators and mutation negatives; corpus expansion remains |
| #91 | preflight | #487 | reject before native allocation; broader allocation audit remains |
| #92 | ownership | #484/#487 | native adoption and export isolation |
| #93 | replay | #483/#487 | strict JSON and rejection-before-allocation |
| #94 | verification scope | #486/#487 | selected versus complete and planted defects |
| #105 | API typing | #483/#488 | compatibility/typing CI and inventory freeze; no public additions |
| #56 | symbolic layers | #468/#486 | reused parameter identity/ordered wires and sweep |
| #151 | amplification | #486 | full multi-mark operator and prepared-state reflection |
| #152 | state preparation | #486 | complex zero-input state preparation and reflection |
| #153 | oracle composition | #486 | reversible composed block and multi-mark oracle; cost evidence remaining |
| #154 | Pauli parity | #486 | existing parity oracle + new reflection/phase tests; Y/ordered parity cost remaining |
| #189 | controlled synthesis | #486 | strict relative phase of controlled reflection |
| #293 | variational | #486 | overlap and multi-observable objectives; molecular source/optimizer history cost still needed |
| #294 | reversible logic | #486 | inverse equivalence and replay; modular arithmetic cost review remains |
| #155 | syndrome | #486 | phase-flip syndrome in addition to existing bit-flip recovery |
| #157 | feed-forward | #486 | native gate-only route; no unapproved if_apply API |
| #298 | verification applications | #486/#487 | reversible defect/witness and replay |
| #460 | atlas | #486 | 23→30 candidate pointers, target 100 remains |
| #352 | functional acceptance | #486/#488 | bounded local capability matrix; device execution not admitted |
| #345 | expressivity epic | #468/#485/#486/#488 | coordinate candidate evidence without closing parent |
| #107 | onboarding | #488 | executable qualification route and tutorial guidance |
| #462 | study packet | #488 | counterbalance and machine-checkable assignment; reviewer freeze pending |
| #165 | external study | #488 | protocol only; real participants and independent review pending |
| #110 | distribution | #488 | archive contents/metadata checker; manual notice review pending |
| #100 | controlled host | #488 | authorized isolated host required; runner manifest prepared |
| #258 | integration | #488 | exact hashes and integration evidence; current push CI not observed |
| #35 | alpha release | #488 | qualification checklist; explicit separate authorization required |

Exact CI and integrated-tree comparison are mandatory. Preserve negative
results and don't add APIs for the sake of closing tickets. External
participant sessions, independent review, legal notice review and authorized
dedicated hardware are not fabricated or replaced with shared CI. No
release/tag/publication authorization. Historical #482 artifacts remain
linked in the qualification ledger.
