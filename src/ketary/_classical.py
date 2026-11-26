"""Bounded native local shot execution, separate from pure Result snapshots."""
from dataclasses import dataclass
from ._validation import _int,_limit,ResourceLimit,UnsupportedOperation

@dataclass(frozen=True)
class ShotResult:
    shots: int
    num_clbits: int
    seed: int | None
    _counts: tuple[tuple[str,int], ...]

    measurements: tuple[tuple[int,int,int], ...] = ()
    backend: str = "unknown"
    backend_version: str = "unknown"

    @property
    def measured_bits(self):
        return tuple(sorted({bit for _,_,bit in self.measurements}))

    @property
    def counts(self):
        return dict(self._counts)

    def probabilities(self):
        """Empirical frequencies, not exact Born probabilities."""
        return {label:count/self.shots for label,count in self._counts}


def run_shots(circuit,*,shots,seed,max_bytes):
    qc=circuit._qc
    if not qc.num_clbits or qc.parameters:
        raise UnsupportedOperation("shot execution requires a bound classical circuit")
    shots=_int(shots,1)
    if shots>10000 or qc.num_qubits>12 or qc.num_clbits>12 or len(qc.data)>1024:
        raise ResourceLimit("dynamic execution: <=12 wires/bits, 1024 instructions, 10000 shots")
    _limit(qc.num_qubits,budget=max_bytes)
    if seed is not None:
        seed=_int(seed)
        if seed>2**32-1:
            raise ValueError("seed exceeds unsigned 32-bit range")
    if not any(item.operation.name=="measure" for item in qc.data):
        raise ValueError("classical circuit requires a measurement")
    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise UnsupportedOperation("install ketary[dynamic] for local shot execution") from exc
    from qiskit import transpile
    backend=AerSimulator(method="statevector",max_parallel_threads=1)
    compiled=transpile(qc,backend=backend,optimization_level=0,seed_transpiler=seed)
    result=backend.run(compiled,shots=shots,seed_simulator=seed).result()
    if not result.success:
        raise RuntimeError("native shot execution failed")
    counts=result.get_counts()
    if (sum(counts.values())!=shots or any(len(label)!=qc.num_clbits or set(label)-{"0","1"}
        or type(count) is not int or count<=0 for label,count in counts.items())):
        raise RuntimeError("unexpected native count schema")
    from importlib.metadata import version
    measurements=tuple((i+1,qc.find_bit(item.qubits[0]).index,qc.find_bit(item.clbits[0]).index)
                       for i,item in enumerate(qc.data) if item.operation.name=="measure")
    return ShotResult(shots,qc.num_clbits,seed,tuple(sorted(counts.items())),measurements,
                      "qiskit-aer/statevector",version("qiskit-aer"))
