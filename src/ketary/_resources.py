"""Logical circuit resource summaries and opt-in textual visualization."""
from dataclasses import dataclass
from ._validation import _int, ResourceLimit

@dataclass(frozen=True)
class ResourceReport:
    num_qubits: int
    gate_count: int
    depth: int
    two_qubit_gates: int
    three_plus_qubit_gates: int
    by_gate: tuple[tuple[str,int], ...]

class _Resources:
    def __init__(self,circuit):
        self._c=circuit

    def summary(self):
        """Logical metrics only; not a hardware cost or transpilation estimate."""
        native=self._c._qc
        by_gate=tuple(sorted((name,int(count)) for name,count in native.count_ops().items()))
        arities=[item.operation.num_qubits for item in native.data]
        return ResourceReport(
            native.num_qubits,len(arities),native.depth(),
            sum(a==2 for a in arities),sum(a>=3 for a in arities),by_gate
        )

class _Visualize:
    def __init__(self,circuit):
        self._c=circuit

    def text(self, *, max_qubits=32, max_gates=512):
        """Return the native text drawing without simulation or mutation."""
        if self._c.num_qubits>_int(max_qubits,1) or len(self._c._qc.data)>_int(max_gates):
            raise ResourceLimit("circuit drawing exceeds logical size limit")
        return str(self._c._qc.draw(output="text",fold=-1))


    def svg(self,*,max_qubits=12,max_gates=64):
        """Return a bounded ordered-wire schematic without execution."""
        from ._visualization import circuit_svg
        return circuit_svg(self._c,max_qubits=max_qubits,max_gates=max_gates)
