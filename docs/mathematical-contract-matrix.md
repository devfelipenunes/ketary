# Mathematical contract traceability — first pass

Baseline 6f1e8a8bbd25882fbdfaa4dc8d7152891dc0450b. 19 contract families, 30 classified public
declarations linked to representative positive and negative test nodes.
The denominator of 330 includes nonnumerical entries, types, properties
and aliases. Do not read this as a mathematical coverage percentage.
Each family still needs per-entry review of domain, conditioning, error,
resource bounds and oracle independence. References are examples, not proof.
The JSON registry is checked for valid public names, duplicate links and
existing test definitions. It does not establish that all linked tests cover
every declaration or that a test passes.

| Family | Contract | Positive reference | Negative/boundary reference |
| --- | --- | --- | --- |
| born (4 entries) | Born rule and Hermitian expectation/variance; normalized pure state | `tests/test_production_math_oracles.py::test_born_and_pauli_expectation_variance` | `tests/test_production_math_oracles.py::test_semantic_sentinels_detect_wrong_results` |
| reduced (4 entries) | Partial trace, Schmidt singular values, base-two entropy and purity; ordered subsystem | `tests/test_production_math_oracles.py::test_reduced_density_schmidt_entropy` | `tests/test_resource_bounds.py::test_svd_limits_before_allocation` |
| algebra (3 entries) | Complex Pauli products; compensated aggregation; bounded terms | `tests/test_production_pauli_robustness.py::test_pauli_algebra_dense_oracle` | `tests/test_production_pauli_robustness.py::test_overflow_not_silently_accepted` |
| embedding (1 entries) | Ordered absolute wire embedding with unchanged source | `tests/test_production_final_mutants.py::test_asymmetric_embedding` | `tests/test_production_final_mutants.py::test_overlapping_tensor` |
| commuting (1 entries) | Strict exp(-itH) for commuting real Pauli sum | `tests/test_production_math_oracles.py::test_exact_commuting_evolution_strict_phase` | `tests/test_dx_coverage_promotions.py::test_product_formula_rollback` |
| dense_evolution (1 entries) | Full operator equality, including phase; <=5 wires | `tests/test_production_workflow_batch2.py::test_two_site_hubbard_number_conservation` | `tests/test_production_workflow_batch2.py::test_dense_hamiltonian_bad_native_output_fails_atomically` |
| product (1 entries) | Ordered finite Lie/Strang approximation; no implicit accuracy guarantee | `research/probes/test_commutator_bound_study.py::test_seeded_multiterm_commutator_bound` | `tests/test_dx_coverage_promotions.py::test_product_formula_rollback` |
| jacobian (1 entries) | Occurrence chain rule for supported ideal generators | `tests/test_production_math_oracles.py::test_shared_jacobian_against_closed_form` | `tests/test_production_exact_coverage.py::test_differential_preflight` |
| hessian (1 entries) | Observable/parameter/parameter tensor; second-order chain rule | `tests/test_production_hessian.py::test_nonlinear_shared_hessian` | `tests/test_production_hessian.py::test_hessian_invalid_preflight` |
| qgt (1 entries) | Projected pure-state Gram tensor; phase gauge, singular directions | `tests/test_production_qgt.py::test_qgt_controlled_shared_and_phase` | `tests/test_production_qgt.py::test_qgt_preflight_no_execution` |
| channel (1 entries) | Finite local CPTP map; ordered wires and budget | `tests/test_production_local_channels.py::test_local_channel_dense_oracle` | `tests/test_production_local_channels.py::test_local_channel_budget_and_invalid_before_execution` |
| complex (1 entries) | Finite complex expectation without dense matrix | `tests/test_production_channels_complex.py::test_complex_pauli_expectation` | `tests/test_production_channels_complex.py::test_complex_expectation_preflight_and_cancellation` |
| preparation (1 entries) | Requested normalized vector on zero input; full native synthesis checked | `tests/test_production_dense_and_dynamic.py::test_arbitrary_state_preparation` | `tests/test_production_dense_and_dynamic.py::test_preparation_invalid` |
| unitary (1 entries) | Finite unitary matrix; strict synthesis | `tests/test_production_dense_and_dynamic.py::test_arbitrary_unitary` | `tests/test_production_dense_and_dynamic.py::test_matrix_invalid` |
| synthesis (2 entries) | Bounded full operator residual, including controlled relative phase | `tests/test_dx_coverage_promotions.py::test_control_phase` | `tests/test_production_native_faults.py::test_synthesis_wrong_operator_never_accepted` |
| dynamic (2 entries) | Nested native condition truth table and expanded preflight | `tests/test_production_nested_dynamic.py::test_nested_truth_table` | `tests/test_production_nested_dynamic.py::test_nested_forbidden_leaves_even_in_unreachable_branch` |
| projection (1 entries) | Independent ideal projection and preserved native structure | `tests/test_production_annotated_projection.py::test_annotated_projection_structural_and_math` | `tests/test_production_annotated_projection.py::test_bad_metadata_rejected_before_copy` |
| witness (2 entries) | Reproducible fixed witness; bounded local deletion | `tests/test_witness_restart_minimization.py::test_restart_revisits_previously_rejected_deletion` | `tests/test_witness_restart_minimization.py::test_budget_retains_reproducible_witness_without_minimality_claim` |
| compare (1 entries) | Sample-only matching inconclusive; dense check separate | `tests/test_verification_workflow.py::test_ladder_never_promotes_samples_to_universal_pass` | `tests/test_verification_workflow.py::test_inputs_validated_before_run` |

Remaining: review each numerical operation (including gate semantics, sampling,
decoders, metrics and query plans), explicit unsupported cases, near-singular
and nonfinite values, strict vs phase-insensitive scopes. No automatic status
promotion. The lifecycle registry remains the full public API inventory.
