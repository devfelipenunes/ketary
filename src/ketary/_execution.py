"""Private native ideal evolution. Facade validates mode and payload first."""
from ._adapter import _sdk
from ._result import Result

def execute_ideal(qc,initial_state,max_bytes):
    _,SV=_sdk()
    if initial_state is None:
        return Result(SV.from_instruction(qc).data)
    if isinstance(initial_state,str):
        if len(initial_state)!=qc.num_qubits or set(initial_state)-{"0","1"}:
            raise ValueError("invalid initial basis label")
        state=SV.from_label(initial_state)
    else:
        if isinstance(initial_state,Result):
            snapshot=initial_state
        else:
            # Reject mismatched array shape before a complex128 copy.
            import numpy as np
            array=np.asarray(initial_state)
            if array.shape!=(1<<qc.num_qubits,):
                raise ValueError("initial state width mismatch")
            snapshot=Result(array)
        if snapshot.num_qubits!=qc.num_qubits:
            raise ValueError("initial state width mismatch")
        state=SV(snapshot.math.statevector(max_bytes=max_bytes))
    return Result(state.evolve(qc).data)
