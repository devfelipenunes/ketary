# Alpha application atlas reconciliation (#460)

Base combined candidate 72a2e92a3f0935fa084135fec422489c9dbee466: 32 indexed intents. This adds 29 already implemented, executable authored intents (61/100 candidate). No new algorithm implementation is asserted. Twenty-two are existing production workflow tests; seven are paired QML/constrained optimization workflows with explicit selectors and existing parameterized tests. All are distinct by objective or output contract, not by width, angle, seed, method variant or test count. Exact combined CI of the prior candidate is a prerequisite, then qualify this successor head separately.

| Intent | Reference | Oracle scope |
|---|---|---|
| graph-stabilizer-defect | `tests/test_production_workflow_batch1.py::test_graph_cycle_stabilizers` | cycle graph stabilizers and planted phase defect; analytic |
| dicke-fixed-excitation | `tests/test_production_workflow_batch1.py::test_dicke_weight_two` | normalized fixed-excitation state and phase negative |
| ramsey-quadrature-estimation | `tests/test_production_workflow_batch1.py::test_ramsey_two_quadratures` | analytic sine/cosine quadrature readout |
| spin-echo-refocusing | `tests/test_production_workflow_batch1.py::test_spin_echo_refocusing` | free evolution versus echo, analytic return probability |
| chsh-correlation | `tests/test_production_workflow_batch1.py::test_chsh_quantum_correlation` | Tsirelson value and separable negative |
| dephasing-coherence-decay | `tests/test_production_workflow_batch1.py::test_dephasing_channel_preserves_population` | analytic density off-diagonal damping and population |
| entanglement-witness | `tests/test_production_workflow_batch1.py::test_mixed_basis_entanglement_witness` | analytic witness on Bell and product state |
| deutsch-jozsa-promise | `tests/test_production_workflow_batch2.py::test_deutsch_jozsa_promise_classification` | constant versus balanced promise; analytic marginal |
| swap-test-overlap | `tests/test_production_workflow_batch2.py::test_swap_test_overlap` | analytic overlap measurement, not overlap optimization |
| hadamard-complex-matrix-element | `tests/test_production_workflow_batch2.py::test_hadamard_test_complex_matrix_element` | analytic complex matrix element |
| full-adder-sum-and-carry | `tests/test_production_workflow_batch2.py::test_reversible_full_adder` | all basis columns, XOR outputs; distinct carry contract from modular addition |
| reversible-linear-transform | `tests/test_production_workflow_batch2.py::test_reversible_linear_map` | full independent GF(2) permutation |
| coherent-entanglement-swapping | `tests/test_production_workflow_batch2.py::test_coherent_entanglement_swapping` | analytic remote Bell reduced density, not teleportation |
| four-qubit-error-detection | `tests/test_production_workflow_batch2.py::test_four_qubit_error_detection_code` | four logical basis states, all single-Pauli faults |
| two-qubit-pauli-tomography | `tests/test_production_workflow_batch2.py::test_two_qubit_pauli_tomography` | Pauli reconstruction against pure-state density |
| helstrom-state-discrimination | `tests/test_production_workflow_batch2.py::test_helstrom_binary_state_discrimination` | analytic optimal binary discrimination success |
| coined-quantum-walk | `tests/test_production_workflow_batch2.py::test_discrete_quantum_walk_cycle` | independent shift/coin matrix powers |
| hubbard-number-conservation | `tests/test_production_workflow_batch2.py::test_two_site_hubbard_number_conservation` | independent many-body dense Hamiltonian, number sector |
| quantum-fisher-metrology | `tests/test_production_workflow_batch2.py::test_quantum_fisher_metrology_scaling` | analytic GHZ vs separable Fisher scaling |
| rank-deficient-natural-gradient | `tests/test_production_workflow_batch2.py::test_natural_gradient_rank_deficient_update` | analytic pseudoinverse update and objective improvement |
| discrete-geometric-phase | `tests/test_production_workflow_batch2.py::test_discrete_geometric_phase_loop` | analytic cyclic state overlap product |
| depolarizing-fixed-point | `tests/test_production_workflow_batch2.py::test_depolarizing_fixed_point` | analytic channel contraction and mixed fixed point |
| qml-angle-classification | `research/qml_workflow_qualification.py::evaluate [angle]` | trained angle classifier, held-out analytic labels and native route |
| qml-parity-classification | `research/qml_workflow_qualification.py::evaluate [parity]` | two-feature parity labels, analytic and native route |
| qml-fidelity-kernel | `research/qml_workflow_qualification.py::evaluate [kernel]` | analytic kernel scores and native route |
| qml-expectation-regression | `research/qml_workflow_qualification.py::evaluate [regression]` | analytic regression scores and native route |
| qaoa-independent-set | `research/constrained_qaoa.py::evaluate [independent_set]` | independent set feasibility and exact classical minimum |
| qaoa-vertex-cover | `research/constrained_qaoa.py::evaluate [vertex_cover]` | vertex-cover feasibility and exact classical minimum |
| qaoa-cardinality-portfolio | `research/constrained_qaoa.py::evaluate [portfolio]` | cardinality constraint and risk-return objective, exact classical minimum |

Deliberately excluded duplicate BV/Simon/QPE/superdense/teleportation/Grover cases, modular increment variants, Heisenberg/XY repetitions, coherent repetition-code variants, single-gate lowering, native-only metadata/barrier checks, BB84 basis sifting (not complete protocol), and generated gate/parameter variants. Full adder is distinct from modulo register addition (carry and sum outputs vs no carry). Swap test is distinct from variational overlap minimization (probability estimator vs optimizer). CHSH and witness are distinct outputs. Dephasing and depolarizing fixed point are distinct channel observables and invariants, not parameter variants. No independent usability or paired native timing claim for the analytic-only tests. Pointer validation alone does not establish execution; preserve the existing full suite and all negative controls. Remaining 39 distinct intents require further implementation or source audit. No release or API change.
