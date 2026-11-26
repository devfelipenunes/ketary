# Agent readability pilot (research only)

Compare the same tasks on native Qiskit, current Ketary, and research-only
inspection/evidence/check aggregation helpers. All snippets are authored
with both APIs visible; lexical tokens/lines are descriptive, not model token
counts, cognitive load or pass@1. No independent LLM or human trial.

Static AST experiment only reads a literal subset of existing Ketary source
without executing it. Unsupported dynamic Python abstains. It is not a DSL,
a general Python analyzer, or production functionality. Runtime inspection
uses a full Qiskit copy, even if the report is bounded; improve that before
adopting it. The aggregate check does not run circuits.

Future blinded study: equal supported tasks and output contracts; balanced
documentation conditions (none, compact card, reference), randomized task
order, independent sessions, multiple models and repeated trials, execution
correctness, hallucinated API calls, exact wire/phase diagnosis, repair turns,
token usage and abstention. Test generated programs in isolated environments
without credentials/network. Compare Qiskit and Ketary on equal tasks; do
not count unsupported hardware/measurements as supported. Include mutation
tests for wrong wires, phase, inverse and misleading tests. Keep held-out
cases separate from documentation and report confidence intervals.

References: https://arxiv.org/abs/2406.14712 (Qiskit HumanEval);
https://arxiv.org/abs/2604.08570 (QuanBench+);
https://www.amazon.science/publications/on-mitigating-code-llm-hallucinations-with-api-documentation.
