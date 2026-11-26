# Integrated research candidate and KetaryEval v0.2

This branch alone experiments with direct gate aliases on the same Circuit,
paginated inspect(), Result.evidence(), Result.verify(), and serializable
check/trace reports. None is approved for main. Existing .gates remains.
The inspector indexes requested operations without making a full native copy;
pages describe a mutable circuit at call time, so do not modify between pages.
Reports are bounded in number of rows, not absolute CPU/RSS. Complex amplitudes
are real/imaginary pairs; probabilities are normalized; trace scope is explicit.
Empty verification is UNSUPPORTED. Native objects are trusted input.

The literal source reader recognizes a narrow grammar in both Qiskit and
Ketary, including chained Ketary construction and source positions.
It abstains on dynamic syntax and never executes source. This is not a
Python analyzer or sandbox. Direct aliases are a candidate, not available
on main. Runtime inspection is preferred for arbitrary Python.

## KetaryEval calibration

12 tasks: 4 generation, 4 comprehension, 3 repair, 1 diagnosis.
Each has an authored reference and deliberate incorrect response.
Code answers are parsed and rebuilt using allowlisted gates; full operators
are checked with strict global phase. Structured answers are exact matched.
No arbitrary generated Python is executed. The public calibration corpus
is not hidden or independent model evaluation.

```bash
python research/agent_readability/ketary_eval.py --self-test
python research/agent_readability/ketary_eval.py --compare-syntax
python research/agent_readability/ketary_eval.py --prompts ketary > prompts.json
python research/agent_readability/ketary_eval.py --grade responses.json
```

Responses: JSON array with id, framework, response (code or answer).
Collect independent responses in fresh sessions; match model version,
temperature, context length, time limits and tool access; randomize tasks,
balance conditions (no docs, concise card, full reference), record actual
input/output tokens and repair rounds. The prompt export currently includes
the constructor/gate prefix for code tasks; other documentation conditions
must be separately controlled. The grader reports per-case statuses; score
pass@1 and abstention separately. Do not exclude malformed responses or
unsupported outputs from denominators. Preserve prompts and raw responses.
For general Python use isolated, no-network, no-credentials environments,
not the restricted grader. Run unseen tasks for a real study. No provider API
credentials or paid model calls are required by these fixtures.

## Compact candidate API card (not production)

- Python 3.12, Qiskit authoritative; q.Circuit(n), q.bell(), q.ghz(n).
- Gate calls mutate and return same Circuit. Existing c.gates.h(0);
  candidate c.h(0).cx(0,1). Angles radians, control before target.
- c.run() returns independent ideal snapshot. No hidden execution in inspect,
  evidence or verify. c.inspect(start=0,limit=32) gives operation pages.
- r.evidence(bits=["00","11"],paulis=["ZZ"]) returns JSON-ready evidence.
- r.verify(probabilities={"00":0.5},expectations={"ZZ":1},normalized=True)
  gives individual and aggregate statuses. No assertion of unrequested properties.
- c.test.equivalent(other) compares full operators with strict phase; max 8q.
  r.test.state(other) compares states; distribution is weaker than state.
- c.debug.compare(reference).to_dict() reports aligned checkpoints only;
  not proof of root cause. Max 8q/256 steps by default.
- Highest wire first for labels, explicit order for marginals.
- Unsupported hardware, classical bits, mid-circuit measurement, noise,
  symbolic parameters, custom gates and arbitrary Python static parsing.

## MCP exploration

A future adapter could expose read-only inspect/evidence/diagnose tools over
bounded replay JSON; no arbitrary source execution, no implicit simulation,
and explicit session authorization for any state changes. Keep it separate
from the core SDK. This is an interface hypothesis, not a deployed MCP server.

## Decision rule

Compare direct gate aliases vs existing .gates: less syntax may increase API
surface and ambiguity. Prefer structured inspection/evidence if they reduce
interpretation errors without duplicating the mathematical engine. Require
independent model and human studies before claims of improved comprehension.
No merge, publication, or PR #20 implied by this experiment.
