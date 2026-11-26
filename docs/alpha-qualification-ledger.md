# Alpha performance qualification ledger

Commit SHA identifies a source tree, not an authentication signature or a
release authorization. Artifact SHA-256 identifies the downloaded ZIP.
CI success alone does not approve a runtime regression. Shared runner
measurements are diagnostic, not dedicated-host evidence.

| PR | Qualified head | Decision | SDK run |
|---|---|---|---|
| #470 | 5bde7290b41cd030bdf8dcdbaaa122f602a23620 | Integrated, weighted expectation | 45885634434 |
| #472 | 7922d11f6639ede1e7f2038712f72db8f824cc7c | Integrated, zero residual SVD | 45887650429 |
| #468 | 4e8262e101631d1fdd01bdd9eb06f11748fe94b0 | Hold, dense regression | 45890056097 |
| #473 | d1beb58e15d7caf780ec36d031804178ae20a377 | Closed unmerged, slower trace | 45890800574 |
| #475 | bbd8ab852d4c05d322462c2a72e3fbc810f48bf5 | Closed unmerged, weak gain | 45888381738 |
| #476 | e426b42d0e57c75dd9cb37a79ba3b5ac227a6c90 | Closed unmerged, weak gain | 45888475693 |
| #477 | b784a61a88e262b2594b4e2021bdb53420de71c4 | Candidate, selective commutator runtime | 45890952600 |
| #478 | 8849866635ca1a790ed151dda1eb1970690fe60a | Candidate, logical native fields | 45891108953 |
| #480 | b1c78a03d8e1ded0ffa05a04be5a8e58d10b8d2a | Research only; retain baseline | 45890690806 |
| #481 | 184db7f4c02bc987eb8c44e2f7b746c7726d35cb | Candidate, synthesis fallback and chunk research | 45891207971 |

Archived benchmark ZIP digests (SHA-256):

| PR | Artifact ID | Digest |
|---|---|---|
| #468 | 15151197627 | ed586996bdf828a0c84633b32c76d6d3978dd6f826684ed7cb5680a75866c8e1 |
| #473 | 15151203623 | b67080b58852b941b11cca75eafce474bcb967e95e7868004091c4552967548c |
| #475 | 15151371743 | 129bc3161770d24272b7ed7d5770d32fff5958a45427034e62848a05ddb7e6fb |
| #476 | 15151805562 | 7861d7a8fbf9f070ea5a1b0441b8178baf1e4c921b3ec2b0eb25f7cef8f2bf13 |
| #477 | 15150829941 | 49350b866c713d519cc67ea57d5e190d53c3abf8f81e70009b68bd681e590dbc |
| #478 | 15151393426 | bc34abecff2e42a30d011815fdb0f7a81b71f5067b1416c75c6e5d5963a6a51e |
| #479 | 15150764642 | 57d45a82155bf53581272949a84fac55a5d042f76cc765c63919956ae319f10e |
| #480 | 15151512477 | 44dfc6fe8b7b44e192cae88c65ef1ccf429558d85fad2f93680ef0e6ac1bb844 |
| #481 | 15152535211 | ee2aa398a2d1f911b4e7214ff53d658b71791ce2212eb972a6118aa5c43ecb1e |

The combined candidate must pass exact-head CI and integrated-tree review.
No merge of #468/#473/#475/#476 runtime is authorized by this ledger.
No dedicated host, independent approval, human study, version/tag or
publication is asserted. Research artifacts are not public API.
