"""Private native ideal evolution. Facade validates mode and payload first."""
from ._adapter import _sdk
from ._result import Result

def prepare_initial(n,initial_state):
    """Validate a complete input snapshot before any native evolution."""
    if initial_state is None:
        return None
    if isinstance(initial_state,str):
        if len(initial_state)!=n or set(initial_state)-{"0","1"}:
            raise ValueError("invalid initial basis label")
        return initial_state
    if isinstance(initial_state,Result):
        snapshot=initial_state
    else:
        import numpy as np
        array=np.asarray(initial_state)
        if array.shape!=(1<<n,):
            raise ValueError("initial state width mismatch")
        snapshot=Result(array)
    if snapshot.num_qubits!=n:
        raise ValueError("initial state width mismatch")
    return snapshot


def execute_ideal(qc,initial_state,max_bytes):
    _,SV=_sdk()
    if initial_state is None:
        return Result(SV.from_instruction(qc).data)
    snapshot=prepare_initial(qc.num_qubits,initial_state)
    if isinstance(snapshot,str):
        state=SV.from_label(snapshot)
    else:
        state=SV(snapshot.math.statevector(max_bytes=max_bytes))
    return Result(state.evolve(qc).data)
