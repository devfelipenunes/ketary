# Scalar Pauli normalization clamp

Refs #306 #307 #256. After existing native finite and imaginary checks,
the quotient is a Python float and the stored norm is finite and strictly
positive. Replace scalar np.clip with two scalar comparisons, preserving
bounds [-1,1], signed zero, and explicit native fault rejection. No change
to native computation, validation, normalization, aggregate order or caps.
34 tests compare the previous clip body at representational boundaries and
near-normalized snapshots, and reject native nonfinite values.

Nine paired diagnostic workloads, 4/8/12 qubits and 1/8/32 labels; single
label uses public expectation, other cases use grouped expectations.
Patch only the previous numerical acceptance body outside timed sections
in single-thread research, identical public paths and independent scalar
bit oracle. This measures the clipping change, not the entire #377
revision or the one-item grouped API regression. Shared CI, no universal
speed or RSS claim.
