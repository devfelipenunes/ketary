# KetaryEval v0.3 — public calibration expansion

This research branch adds 168 cases to the 12 legacy calibration cases, leaving
v0.2 and its historical syntax measurements unchanged.

| Capability | Cases |
| --- | ---: |
| Generation | 30 |
| Comprehension | 30 |
| Mathematics | 20 |
| Debugging | 20 |
| Repair | 20 |
| Testing | 20 |
| Optimization | 20 |
| Abstention | 20 |
| Total | 180 |

The corpus is deterministic, public and parameterized. Counts are instances,
not independent task families. Each instance has one authored reference and
one deliberately wrong response per API (540 positive and 540 negative
calibration checks when fully run). These are target counts until CI confirms
them; neither test counts nor calibration scores are model outcomes.

Testing tasks request a structured basis-input/expected-output assertion;
the grader accepts any assertion that passes the intended circuit and kills
the mutant, not just the authored answer. Optimization requires strict
operator equivalence AND a gate budget. Abstention has ten supported and ten
unsupported literal-reader examples. Mathematics and debugging are checked
against Qiskit statevectors and SDK diagnostics. Other code answers are parsed
and rebuilt, not executed. The study is limited to ideal logical circuits,
small widths and the literal-reader grammar; testing does not yet evaluate
arbitrary Python test generation.

## Reproduce

From the repository root, in the pinned Python 3.12 environment:

```bash
python -m pytest -q research/agent_readability
python research/agent_readability/ketary_eval_v03.py --self-test
python research/agent_readability/ketary_eval_v03.py --prompts candidate --condition reference --seed 42 > prompts.json
python research/agent_readability/ketary_eval_v03.py --grade responses.json
```

The response packet is:

```json
{"framework":"candidate","condition":"card","responses":[{"id":"G01","response":{"code":"import ketary as q\nc=q.Circuit(2)\nc.h(0)\nc.cx(0,1)"}}]}
```

A packet is one framework and documentation condition. Missing responses are
counted in the 180-task denominator; duplicate or unknown IDs are rejected.
Output includes category breakdowns, raw verdicts and separately reported
supported/unsupported classification. Model/provider/version, replicate,
actual tokens, latency, and tool budgets still need a separate run manifest.

## Limits and next experiment

The existing documentation conditions mostly equalize semantics and literal
gate construction. They do not yet measure the agent's ability to discover
and actively use inspect(), evidence(), verify(), or diagnostic reports.
A distinct tool-enabled study should compare equivalent capabilities with
matched context and tool budgets, measuring first-attempt correctness,
repair rounds, context usage and unsupported-operation errors. Freeze
versions and collect fresh held-out tasks with family-level splits before
running independent models. Report family-clustered uncertainty and human
results separately. No paid API calls, external model results, or production
API approval are implied here. Keep this experimental work off main.
