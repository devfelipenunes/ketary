# CORE01–CORE10 acceptance

No new algorithms, simulation mode, compiler, DSL, or separate facade.
Existing observable and verification capabilities are aligned through the
current API. This is a candidate engineering checklist, not a release.

| Gate | Implementation and verification |
|---|---|
| CORE01 | Four concepts and canonical flow: core-api.md |
| CORE02 | Complete classified stub inventory; CI detects drift |
| CORE03 | Fluent gates, run, typed reports are canonical; aliases retained |
| CORE04 | Ownership/return/status/error conventions; compatibility regression |
| CORE05 | Observable keys in Contract, Result.verify, grouped checks |
| CORE06 | Common render/JSON export on verdict reports; unchanged scopes and legacy bool |
| CORE07 | README, getting started, tutorial/how-to and installed wheel example |
| CORE08 | Zen and design review criteria |
| CORE09 | Experimental compatibility policy and schema rules |
| CORE10 | Exact-head CI, reviewed merge, post-merge CI and scope freeze |

Required verification: complete native/analytic regression suite and type
consumer, new aggregate expression/legacy schema tests, complete surface
inventory, canonical onboarding smoke. No claim of independent human approval,
dedicated-host benchmark, public release or usability advantage.
