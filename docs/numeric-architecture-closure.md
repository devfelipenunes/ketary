# Numerical validation and Hamiltonian ownership review

Refs #190 #272 #273 #253. Baseline ef2611291f96a3b7d20afcb814c9e8415ebf036f.
Run `python -m research.priority_architecture_audit` and
`python -m research.architecture_inventory` for static counts. The selected
inventory enumerates relative imports, finite-check sites and exact AST-body
duplicates; it is not a call graph or semantic equivalence proof.

| Responsibility | Owner | Decision |
|---|---|---|
| Finite user real scalars | _validation._real | Reject bool and non-Real, normalize conversion exceptions |
| Numeric gate angles | _validation._angle | Preserve float fast path, specific error text, radians |
| Symbolic angles | _adapter._gate_angle | Native ParameterExpression only in explicitly symbolic mode |
| Nonnegative/positive integral bounds | _validation._int | operator.index, reject bool, preserve NumPy integer support |
| Dense payload limits | _validation._limit | integer budget and statevector payload, not RSS |
| Tolerance | _validation._tol | real scalar plus nonnegative restriction |
| Native bound validation | _adapter._validate_bound_values | native float hot path; no need to repeat user input conversion |
| Dense complex input | _transpilation._finite_complex | permits finite complex amplitudes, rejects nonnumeric values |
| Native expectation results | _result._native_pauli_value | validate real and imaginary finite components and imaginary residue; ArithmeticError |
| Observable coefficients | _observable | real aggregate after duplicate cancellation; native complex algebra distinct |

The shared scalar helpers already own identical input semantics. Do not replace
native-result checks with user-input _real (different error boundary), accept
complex angles, or replace complex-array validation with scalar loops. No new
refactor is justified by identical spelling alone.

Hamiltonian routes: _ergonomics._evolve owns exact commuting Pauli construction
and symbolic time/identity phase. _ergonomics._evolve_product owns explicit
ordered first/second-order approximation and bounded steps. _transpilation.
_evolve_dense owns bounded noncommuting exact matrix synthesis (five wires,
native unitary verification). The Circuit facade delegates these three
different contracts. No proposed extraction removes the mathematical mode,
resource or phase differences; retain existing ownership for this cycle.
A future extraction requires a before/after import and performance measurement,
not module-size targets. Independent dense and full-operator tests already
exist in test_pauli_synthesis.py, test_production_dense_and_dynamic.py and
test_product_formula_cost_and_shrink.py. New tests exercise scalar boundaries
and the distinct Hamiltonian modes together. No API or error policy change.
