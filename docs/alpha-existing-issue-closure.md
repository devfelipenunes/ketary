# Existing-issue closure evidence

Baseline main 990a519896a3eb2d79605ad3468130b3644b8477; existing PR #493 is the integration vehicle.
No new issues or PRs were created. The three incoming heads each passed
all six SDK jobs; this combined tree still requires its own CI.

| Issue | Source candidate | Decision |
|---|---|---|
| #97 | c7c4fb499ac03bd493405f2265b888fa3c9f01fc | Keep mapping binding, qualify native identity and ownership; #468 rejected on dense regressions. |
| #294 | 61225bcb86bae7c41c5d08f75048c1256da85c7b | Four reversible workflows now represented, addition profiled against ModularAdderGate. |
| #154/#303 | 203c8f77d1888c6e20cbc1275b4db8bf99fe34b7 | Keep mixed-basis parity research; do not promote until symbolic/resource/ownership and matched scope checks. |
| #105 | existing inventory and signature tests | Retain all 330 classified declarations (94 Core, 182 Advanced, 20 Native, 34 Compatibility); no removal or new spelling. |
| #107 | executable documentation and clean-wheel check | Extend missing GHZ/BV/Simon/QAOA recipes, retain scope/budgets. |
| #460 | application atlas | 31 distinct inventoried authored intents; not 100 or independent participants. |

Paired benchmark observations, pooled p50, shared CI (not controlled host):
- #491 modular addition, 1/2/3 bits per register: Ketary common gates 1/17/64,
  native library 1/35/72; build ms .047980/.078428/.182875 vs
  .052319/.056607/.060284; run ms .179179/.270811/1.588288 vs
  .194227/.922762/1.395094. Native source 32 vs Ketary 129 tokens,
  so no claim of universal expressivity or speed. Artifact 15153223768,
  SHA256 9475d98001cd8f5e7e1febb23d30c253f9e8974ccecf54c992880b19812e707f.
- #493 mixed local basis, 4/5/6 wires: baseline common gates 29/60/82,
  shared 19/34/48; CX 12/24/40 -> 8/16/26, depth 21/42/54 -> 13/26/39;
  build .258880/.402246/.512452 -> .263668/.351741/.474175 ms;
  run .664712/1.272398/1.708445 -> .471291/.743761/1.056693 ms.
  Native library build excludes lowering; its execution is not matched
  to a prelowered circuit. Artifact 15153756151 SHA256
  685d570120515998c3e6a30f939cc4e5ddb5014bf58c6d39031ab30a223b734c.

The API inventory baseline and current counts agree. Signature parity,
overload coverage, lifecycle, admission policy, strict mypy, ordered-wire
compatibility and legacy schema/verdict checks remain CI requirements.
This is an authored technical review, not live usage telemetry or
independent review. No public version change, release, hardware claim or
scope expansion. The dedicated-host, independent study and license review
gates remain open.
