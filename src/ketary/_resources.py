"""Logical circuit resource summaries and opt-in textual visualization."""
from dataclasses import dataclass

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

    def text(self):
        """Return the native text drawing without simulation or mutation."""
        return str(self._c._qc.draw(output="text",fold=-1))
