# Semantic engineering research: I02–I10

## Prior art and hypothesis

Quantum assertions, program verification, debugging and repair already exist.
Proq (https://doi.org/10.1145/3428218) studies projection-based runtime
assertions on quantum computers. AssertsQ (https://www.insticc.org/node/TechnicalProgram/iqsoft/2025/presentationDetails/135533)
integrates assertion debugging with Qiskit. Twist (https://doi.org/10.1145/3498691)
studies purity and entanglement reasoning. Bugs4Q
(https://www.sciencedirect.com/science/article/am/pii/S0164121223002005)
offers real bug fixtures. Qiskit HumanEval (https://arxiv.org/abs/2406.14712)
benchmarks quantum code generation, not human participants. Practitioner
research (https://arxiv.org/abs/2506.17306) motivates empirical DX work.
These are starting points, not an exhaustive novelty review.

The hypothesis is the usefulness of one shared, evidence-oriented interface
for humans and agents: reusable numerical properties, inspectable structure,
diagnostics, and validated proposals. No claim of novel assertions, formal
proof, hardware support, or superiority.

## Research prototypes

- I02: Contract is immutable, width-specific, bounded to 32 predicates and
  verifies only an explicitly supplied Result. Snapshot success is not
  universal operator correctness; operator checks remain separate.
- I03: structural wire dependency graph, bounded to 8 qubits/256 gates;
  literal source correspondence is checked against runtime operations.
  This does not prove execution origin, entanglement or causal influence.
- I04: explicit simulations, state/distribution/strict operator checks and
  optional Pauli evidence; equal-index trace may be unsupported.
- I05: canonical JSON and deterministic human text derived from identical
  checks; report carries scope, tolerance, and contract fingerprint.
- I06: reference-guided single-operation replacement/insertion/deletion,
  <=32 candidates, strict full-operator validation through Qiskit; no
  automatic mutation, ambiguous cases remain ambiguous.
- I09: local read-only registry of bounded immutable replay artifacts.
  Verify/compare calls explicitly simulate; inspect does not. Optional
  stdio MCP wrapper requires separately installed MCP and transport smoke
  testing. Not a deployed multi-user server or authorization system.

These modules are under research/agent_readability rather than production
exports. No new public API or dependency was added.

## Human and agent study protocol (I07/I08)

Primary endpoint: task correctness at fixed first-attempt budget. Secondary
endpoints: time, mathematical explanations, invalid operations, repair
success, tool calls, and actual model tokens (agents only). Human users:
consent, pseudonymous IDs, prior experience strata, standardized tutorial,
counterbalanced order, no credentials or identifying records in repository.
Recruitment and ethics review must be arranged before collection. A pilot
should establish variance and feasibility before a power calculation.
Agent users: pin model/provider/version, temperature and tool budgets;
fresh independent sessions; record raw responses and actual provider usage.
Separate humans and agents; do not pool model versions or documentation arms.

The study_rehearsal module exports six counterbalanced public family-separated
assignments for UX rehearsal and validates complete 180-task run manifests
for full-packet analysis. The assignment bundles are NOT complete per-API
packets and must not be passed to full-packet scoring as if complete.
The analysis is a participant-clustered descriptive bootstrap on full paired
public packets, with missing answers counted as failures. It is tested with
synthetic fixtures only. No recruitment, independent LLM trials, private
held-out task construction, family-clustered inference or power calculation
has happened. For real trials, independently author and sequester families,
freeze the task protocol and API before exposure, use matched conditions and
report confidence intervals with participant AND family clustering as
appropriate. Tool-enabled studies require equivalent tool availability.

## I10 manuscript outline

1. Problem, prior art and explicit semantic boundaries.
2. Architecture and human/agent report views.
3. Deterministic calibration and paired workflow experiments.
4. Preregistered independent human/agent experiments.
5. Ablations: contracts, report detail, diagnostics, tools, context budgets.
6. Results with uncertainty, null/negative findings and limitations.
7. Artifact reproduction and API decision.

Only sections 1–3 have initial evidence. Sections 4–7 require further work;
no scientific paper is ready for submission. No claims of productivity or
model accuracy are justified by authored lexical comparisons.

## Reproduction

Python 3.12 pinned repository environment:

```bash
python -m pytest -q research/agent_readability
python research/agent_readability/study_rehearsal.py --assignment 0
```

Run the optional MCP bridge only in a trusted local environment after
installing and reviewing a compatible MCP dependency; transport remains
unvalidated in this change. No external calls are made by the tests.
