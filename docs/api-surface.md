# Public API surface inventory

All declared public stub entries are classified once; constructors and dunder protocols belong to their types. Inherited methods are listed at their declaring type. The JSON inventory is checked in CI. Categories guide learning, not stability guarantees.

## Core (94)

- **Top-level**: `CheckResult`, `Circuit`, `ComparisonReport`, `Contract`, `Evidence`, `I`, `Observable`, `Result`, `SnapshotReport`, `VerificationReport`, `X`, `Y`, `Z`, `all_pairs`, `bell`, `chain`, `ring`, `star`
- **CheckResult**: `actual`, `detail`, `expected`, `render`, `require`, `status`, `tolerance`
- **Circuit**: `apply`, `apply_each`, `ccx`, `ch`, `contract`, `copy`, `cp`, `crx`, `cry`, `crz`, `cswap`, `cx`, `cy`, `cz`, `h`, `mcx`, `num_qubits`, `p`, `repeat`, `run`, `rx`, `rxx`, `ry`, `ryy`, `rz`, `rzz`, `s`, `sdg`, `swap`, `sx`, `sxdg`, `t`, `tdg`, `test`, `u`, `wires`, `x`, `y`, `z`
- **ComparisonReport**: `evidence`
- **Contract**: `atol`, `expectations`, `normalized`, `num_qubits`, `probabilities`, `verify`
- **Evidence**: `reproduce`
- **Observable**: `num_qubits`
- **Result**: `math`, `num_qubits`, `test`
- **SnapshotReport**: `checks`
- **VerificationReport**: `checks`, `render`, `require`, `scope`, `status`
- **_Checks**: `expectation`, `probability`
- **_CircuitChecks**: `compare`
- **_Math**: `amplitude`, `expectation`, `expectations`, `probabilities`, `probability`, `variance`
- **_Report**: `render`, `require`, `status`

## Advanced (182)

- **CheckResult**: `to_dict`, `to_json`
- **Circuit**: `bind`, `bind_partial`, `capabilities`, `checkpoint`, `checkpoints`, `classical`, `compose`, `compute_action_uncompute`, `control`, `debug`, `decompose`, `diff`, `evolve`, `evolve_exact`, `evolve_product`, `expectation_hessian`, `expectation_jacobian`, `from_json`, `from_unitary`, `if_x`, `if_z`, `inspect`, `inverse`, `measure`, `num_clbits`, `optimize`, `parameter`, `parameter_vector`, `parameters`, `plan`, `prepare_state`, `quantum_geometric_tensor`, `register`, `registers`, `reset`, `resources`, `run_many`, `run_shots`, `sweep`, `sweep_rows`, `symbolic`, `to_json`, `visualize`
- **Contract**: `to_dict`
- **Top-level**: `DiagnosticReport`, `ModalOutcomeReport`, `OperatorMetricsReport`, `PhaseEstimateReport`, `QueryPlan`, `ResourceLimit`, `ResourceReport`, `SemanticDiffReport`, `ShotResult`, `StatisticalContract`, `StatisticalReport`, `SweepPlan`, `TraceComparison`, `TraceStep`, `UnsupportedOperation`, `amplitude_amplification`, `ansatz`, `basis`, `bernstein_vazirani`, `constant_oracle`, `decode_bernstein_vazirani`, `decode_phase_estimation`, `decode_teleportation`, `deutsch_jozsa`, `ghz`, `grover`, `maxcut_hamiltonian`, `parity_oracle`, `phase_estimation`, `phase_oracle`, `qft`, `recover_simon`, `simon`, `superdense`, `teleportation`
- **Evidence**: `from_dict`, `from_json`, `minimize`, `to_dict`, `to_json`
- **ExternalVerificationReport**: `external_equivalence`
- **ModalOutcomeReport**: `label`, `peak_probability`
- **Observable**: `anticommutator`, `on`, `to_dict`
- **OperatorMetricsReport**: `operator_norm`
- **PhaseEstimateReport**: `phase`
- **QueryPlan**: `bits`, `estimate`, `paulis`, `run`, `subsystems`
- **ResourceReport**: `by_gate`, `depth`, `gate_count`, `num_qubits`, `three_plus_qubit_gates`, `two_qubit_gates`
- **Result**: `evidence`, `sample`, `verify`, `visualize`
- **SemanticDiffReport**: `operator`, `render`, `scope`, `structure_equal`, `to_dict`, `to_json`, `zero_input`
- **ShotResult**: `backend`, `backend_version`, `counts`, `measured_bits`, `measurements`, `num_clbits`, `probabilities`, `seed`, `shots`
- **StatisticalContract**: `confidence`, `margin`, `num_clbits`, `probabilities`, `verify`
- **SweepPlan**: `bindings`, `run`
- **TraceComparison**: `actual_operation`, `actual_wires`, `check`, `reference_operation`, `reference_wires`, `step_index`, `to_dict`
- **TraceStep**: `operation`, `result`, `wires`
- **VerificationReport**: `to_dict`, `to_json`
- **_Checks**: `distribution`, `entangled`, `expectations`, `fidelity`, `normalized`, `state`
- **_CircuitChecks**: `equivalent`, `metrics`
- **_Debug**: `checkpoint`, `compare`, `compare_checkpoints`, `trace`, `verify_checkpoints`
- **_Math**: `conditional_probability`, `density_matrix`, `dirac`, `entropy`, `explain_probability`, `fidelity`, `marginal_probabilities`, `norm`, `observable_variance`, `observable_variance_streamed`, `purity`, `schmidt`, `statevector`, `table`, `top_probabilities`, `trace_distance`
- **_Report**: `scope`, `to_dict`, `to_json`
- **_Resources**: `summary`
- **_ResultVisualize**: `bloch`, `bloch_svg`, `histogram`
- **_Visualize**: `svg`, `text`

## Native (20)

- **Circuit**: `append`, `from_dynamic`, `from_parameterized`, `from_symbolic`, `from_synthesized`, `project_annotated`, `run_channel`, `run_density`, `run_noisy`, `to_qiskit`, `transpile`, `transpile_for`
- **Top-level**: `ExternalVerificationReport`, `from_qiskit`
- **Observable**: `commutator`, `from_qiskit`, `product`, `to_qiskit`
- **_CircuitChecks**: `external_equivalence`
- **_Math**: `expectation_complex`

## Compatibility (34)

- **Circuit**: `analyze`, `gates`, `h_many`
- **_Gates**: `ccx`, `ch`, `cp`, `crx`, `cry`, `crz`, `cswap`, `cx`, `cy`, `cz`, `h`, `mcx`, `p`, `rx`, `rxx`, `ry`, `ryy`, `rz`, `rzz`, `s`, `sdg`, `swap`, `sx`, `sxdg`, `t`, `tdg`, `u`, `x`, `y`, `z`
- **_Math**: `observable`
