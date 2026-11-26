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


def execute_ideal(qc,initial_state,max_bytes,*,prepared=False):
    _,SV=_sdk()
    if initial_state is None:
        return Result._from_evolution(SV.from_instruction(qc).data)
    # Only the private batch caller may bypass repeated validation of an
    # exact, already prepared immutable snapshot or basis label. Keep the
    # legacy path for subclasses, whose accessors may have custom behavior.
    trusted=prepared and type(initial_state) in (Result,str)
    snapshot=initial_state if trusted else prepare_initial(qc.num_qubits,initial_state)
    if isinstance(snapshot,str):
        state=SV.from_label(snapshot)
        return Result._from_evolution(state.evolve(qc).data)
    # Pinned Qiskit Statevector.evolve uses shallow copy + new contraction
    # arrays, including out-of-place global phase. Read-only input is
    # borrowed only for the duration of this trusted unitary evolution.
    # Empty/identity outputs may alias; _from_evolution detects that case.
    from ._validation import _limit
    if not trusted:
        _limit(snapshot.num_qubits,budget=max_bytes)
    return Result._from_evolution(SV(snapshot._data).evolve(qc).data,
                                  borrowed=snapshot._data)
