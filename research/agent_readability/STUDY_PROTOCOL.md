# Independent model study: execution protocol

The calibration set is public; it is not a held-out model benchmark. For
a subsequent study construct private held-out analogues with changed widths,
wire order, angles, phase and failure locations. Use the same task families
and independent mathematical oracles. Do not reveal reference answers.

Export randomized task packets:

```bash
python research/agent_readability/ketary_eval.py --prompts qiskit --condition none --seed 42
python research/agent_readability/ketary_eval.py --prompts ketary --condition card --seed 42
python research/agent_readability/ketary_eval.py --prompts candidate --condition reference --seed 42
```

Run all nine API/documentation combinations, not just these examples.
The reference condition supplies a scoped semantic reference for the task
family, not the complete upstream manual. Compare equal documentation
budgets separately if needed. Use one task per independent model session,
same model version/settings/tool budget, randomized order and multiple
repeats. Record request/response tokens from the actual provider. Store
responses as a JSON array, e.g. `[{"id":"C04","framework":"ketary","response":{"answer":"UNSUPPORTED"}}]`.
Use `--grade responses.json` for per-case status. Keep model/version/condition,
seed, replicate, elapsed time, raw response, tokens and repair count in a
separate run manifest. Do not silently drop invalid or unsupported responses.

Primary metrics: first-attempt pass rate and correct abstention on unsupported
tasks. Secondary: diagnostic precision, invalid API calls, repair success,
tokens, latency. Analyze paired tasks across conditions and report sample
sizes, exact denominators and uncertainty (e.g. paired bootstrap across tasks
with clustering by model/session). Do not count repeated deterministic
fixtures as independent model samples. Human testing remains separate.

The grader accepts only a limited literal subset, not arbitrary Python.
General code generation requires a separately isolated environment with
no network/credentials and explicit execution/resource controls. No model
API calls, billing, or model outcome claims are made by this repository.
