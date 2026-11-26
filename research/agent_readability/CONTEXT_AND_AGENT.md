# Reading context and deterministic agent workflow

The prototype reports structured operations directly from the native circuit,
without copying the complete circuit or simulating. A bounded page identifies
offset, next offset, total and omitted operations; mutation between pages is
not supported for consistent traversal.

The read-context benchmark compares extraction of the same first 32 logical
operations from full replay JSON versus direct inspection. It separately
reports serialized full replay and page sizes. These representations are
not equally complete, so reduction is scoped to that particular request.
For math evidence it compares a full probability dictionary with two
selected amplitudes and probabilities. This is a contextual-output size
measurement, not a claim of equivalent full information or token savings.
Timings use 20 randomized paired repetitions on a shared runner.

A deterministic workflow demonstrates inspecting, explicitly running,
comparing distributions/states/operators, examining aligned traces and
validating a trusted repair. It is not a language model or automatic root
cause detector. Agent integration can consume the JSON output; there is
no MCP server, provider credential or arbitrary source execution here.

A future MCP transport can expose read-only tools over replay artifacts:
inspect (no simulation), evidence (requires explicit bounded simulation),
compare (requires explicit scope and resource limits). Tool outputs should
include schema/version, input artifact identity, scope, status, truncation,
tolerance and numerical evidence. Keep the transport outside the SDK;
authorization, quotas, isolation and provenance must be designed before
deployment. No transport is adopted or deployed by this study.
