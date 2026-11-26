# R07 — Paired semantic workflow experiment

The hypothesis is that progressive semantic APIs reduce the authored client
logic needed to extract or verify mathematical facts. This experiment does
not measure human comprehension or LLM performance.

## Design

24 deterministic task instances (6 each): paginated operation inspection,
selected complex amplitudes/probabilities/Pauli expectations, mixed passing
and failing verification predicates, aligned checkpoint diagnosis (including
equal-state/different-gate and unsupported alignment cases).

Three variants receive identical trusted circuits and requests. Qiskit uses
public native QuantumCircuit/Statevector APIs; baseline Ketary uses its
pre-candidate native export, math/test/debug APIs; candidate Ketary uses
inspect/evidence/verify and serializable trace reports. The explicit simulation
occurs once for evidence or verification; inspection is not simulation.
Reference circuit construction is common input scaffolding, not a measured
optimization.

Each variant is checked against the same canonical facts with 1e-9 absolute
tolerance; analytic expectations supplement the native Qiskit comparison.
The raw result may contain extra metadata (scope, tolerance, actual values).
Report canonical and raw JSON bytes separately; raw sizes are not directly
comparable in information content. Code-size counts Python lexical tokens
in the authored workflow functions, including the shared inspection helper
when used, but excluding common input construction, imports and metric
infrastructure. Repeated tasks reuse code: category totals are weighted
workload counts, not independent code samples. Alternative implementations
may be shorter; this is a reproducible comparison, not a minimum-code proof.
No model tokens, timings, memory or speed claims are made.

## Run

```bash
python -m pytest -q research/agent_readability/test_semantic_workflows.py
python research/agent_readability/semantic_workflows.py > semantic-results.json
```

The output includes per-task results and per-category/variant totals.
No external model calls, arbitrary source execution, or network access.

## Next: R08 agent study

Freeze the API version and prepare a held-out task packet with independently
authored families. Compare native, baseline and candidate using equal
documentation/context/tool budgets. A separate condition supplies matched
read-only tools with identical schemas to isolate interface effects from
tool availability. Record actual provider token counts, tool calls, first
attempt pass, final pass, failure modes, and repair rounds. Do not give agents
reference answers. The deterministic results here establish feasibility and
calibrate oracles, not the efficacy of an LLM agent.
