# Qiskit workflow coverage and usability

Goal: preserve professional capability, not win a line-count competition.
The audit uses 37 authored tasks with matched outputs or explicit rejections.
Direct means only the Ketary public API is used for the operation; interop
means explicit Qiskit use or conversion is necessary; gap means a tested
direct route is rejected, not that no mathematical decomposition exists.
Native baseline must execute even for rejected routes. No false PASS,
unsupported cases are not successes. Operator comparisons retain phase.
Single timings are diagnostics, not human task times or benchmarks.

Official reference: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.QuantumCircuit
and https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.SparsePauliOp

Run: python -m research.qiskit_workflow_coverage --output workflow-coverage.json.
Prompt-only export: python -m research.qiskit_workflow_coverage --prompts.
For actual usability, use blinded crossover tasks with independent developers,
matched experience/time limits/docs, random order, success/semantic errors,
time-to-correct-solution, debugging and trust ratings. Record blocked tasks,
native escape hatches and confidence. Separate LLM trial with model/version,
prompt, tool budget and pass@1. Authored fixtures do not measure either.

Prioritize: bounded explicit synthesis/import preserving phase and provenance;
symbolic partial binding and import; composite closed/open controls; explicit
state preparation (unitary vs reset); general operator algebra distinct from
Hermitian observables; noncommuting evolution with declared error contract;
identity/barrier/metadata semantics; typed diagnostics and docs. Dynamic
import/control, mixed states, hardware/noise and general backend support need
separate scoped architectural decisions. No automatic lowering, hidden runs,
unbounded matrices, silent metadata loss or publication.
