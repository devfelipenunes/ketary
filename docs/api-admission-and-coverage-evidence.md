# API admission and coverage evidence

Refs #210 #135. Preserve the admitted 330 classified declarations from
b13780fe; existing stub/surface, lifecycle, canonical replacements,
parameter contracts and compatibility tests remain required. An addition
requires an individual admission row, a promoted decision with all gates
true, explicit mode and separate owner/CI evidence references. This static
guard cannot authenticate an approval or replace PR review; changing the
baseline requires deliberate owner review, not silently editing the
baseline to admit a symbol. No runtime policy engine.

Core and Dynamic CI now emit raw coverage JSON and deterministic
scope-specific gap reports as artifacts. Baseline counts are transcribed
from exact #400 CI job logs, 26 modules per scope. Historical BrPart counts
are partial branch locations, not all missing arcs; compare missing line
counts only, retain current raw missing branch arcs and do not infer old
arc counts. Existing six-decimal 95% combined statement/branch gate is
unchanged. Gap order guides review, never certifies correctness. No new
dependency, exclusions or weakened tests.
