# Local observable remapping experiment

Hypothesis: an ordered embedding operation could reuse the same local
Hamiltonian in different registers for evolution and measurement. Current
canonical evolution already supports apply(local_block,wires=...), so a new
Circuit method alone is redundant. The research helper embed returns an
ordinary Observable, not a second expression representation. Wire i in
the local observable maps to wires[i]. Width is explicit, identity and zero
terms retain width, and input remains immutable.

Compare with current apply and with independently lifted dense matrices.
Research only: no public method, no automatic promotion. Need at least two
real workflows and matched source/cost evidence before changing the API.
