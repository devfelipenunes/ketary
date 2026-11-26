# Production workflow and annotation contract probes

The following 12 executable workflow fixtures have distinct intents in this
new batch: graph stabilizers, Dicke preparation, half adder, modular increment,
Ramsey, spin echo, CHSH, Heisenberg exchange, variational ground state,
coherent repetition-code recovery, dephasing channel and entanglement witness.
Each asserts a closed-form result or independently constructed matrix.
Some overlap earlier task families; do not count them as 12 new global unique
tasks or as independent human evaluation. All remain candidate until CI.

Two additional probes exercise native structural preservation: trusted local
QPY round-trip of metadata/register/ordered barrier/phase and a barrier fence
under target-independent optimization. The strict Ketary import continues
to reject these inputs. A numerically identical operator does not prove
preservation of annotations or scheduling intent. No untrusted QPY loading,
public serialization schema change, implicit projection, or new mutable IR.

Candidate future acceptance: bounded JSON-compatible metadata with defensive
ownership, declared barrier placement and register semantics, explicit policies
for copy/bind/compose/control/optimization/trace/replay and target compilation;
negative tests for unsupported combinations. The native object remains
authoritative. Keep current strict import unchanged until that contract is
qualified. Native QPY evidence alone does not raise 35/37 Ketary task coverage.
