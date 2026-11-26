# Parameter semantics decision — #97

Keep the integrated mapping-based sweep after three sparse-plan candidates
failed dense performance qualification (#468). The native circuit remains
authoritative. No topology cache, implicit parameter renaming, alternate IR
or relaxation of validation is justified. Existing full binding and partial
binding paths are intentionally distinct: partial binding retains parameter
identity, while a full numeric assignment validates all evaluated gate
angles and phase. Sweeps zip native-ordered finite rows before assigning
independent bound circuits, and never execute implicitly.

The closure corpus adds independent native parameter-vector expressions,
symbolic global phase, complete/partial/named/ordered binding and both
sweep routes, reversed wire order, independent payloads and exported
bindings, same-name/different-identity rejection, invalid late values
before assignment, expression singularity and unbound execution/replay
rejection. Seeds 713/2909/8017 are authored deterministic cases, not
independent human evaluation. Existing archived binding profiles and
negative #468 remain the evidence of the performance decision. No new
runtime or API change. Review exact-head CI and integrate before closing
the semantic issue. #56 held-out writing study and #52/#100 controlled
performance evidence are separate.
