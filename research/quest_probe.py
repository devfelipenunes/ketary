"""Research-only direct CPU QuEST bridge, using the pinned public C++ API."""
import ctypes as ct
from pathlib import Path
from threading import Lock
import numpy as np
from qiskit import QuantumCircuit

OPCODES={"h":0,"x":1,"y":2,"z":3,"rx":4,"ry":5,"rz":6,
         "cx":7,"cz":8,"swap":9,"p":10}
ANGLED={"rx","ry","rz","p"}
TWO={"cx","cz","swap"}
_I=np.ctypeslib.ndpointer(dtype=np.int32,ndim=2,flags="C_CONTIGUOUS")
_D=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags="C_CONTIGUOUS")
_LOCK=Lock()
_USED=False

def pack(circuit):
    if not isinstance(circuit,QuantumCircuit):
        raise TypeError("expected native QuantumCircuit")
    n=circuit.num_qubits
    if not 1<=n<=22 or len(circuit.data)>100000 or circuit.num_clbits or circuit.parameters:
        raise ValueError("unsupported width, operation count or execution mode")
    rows=np.empty((len(circuit.data),3),dtype=np.int32)
    angles=np.zeros(len(rows),dtype=np.float64)
    from qiskit.circuit.library import (HGate,XGate,YGate,ZGate,RXGate,RYGate,RZGate,
                                       CXGate,CZGate,SwapGate,PhaseGate)
    types=dict(zip(OPCODES,(HGate,XGate,YGate,ZGate,RXGate,RYGate,RZGate,
                           CXGate,CZGate,SwapGate,PhaseGate),strict=True))
    for i,entry in enumerate(circuit.data):
        op=entry.operation
        name=op.name
        if name not in OPCODES or op.base_class is not types[name] or entry.clbits:
            raise ValueError(f"unsupported QuEST probe operation: {name}")
        if name in {"cx","cz"} and op.ctrl_state!=1:
            raise ValueError("open control unsupported")
        wires=[circuit.find_bit(w).index for w in entry.qubits]
        if len(wires)!=(2 if name in TWO else 1) or len(set(wires))!=len(wires):
            raise ValueError("invalid wire mapping")
        if len(op.params)!=(1 if name in ANGLED else 0):
            raise ValueError("invalid gate parameters")
        rows[i]=(OPCODES[name],wires[0],wires[1] if len(wires)==2 else -1)
        if name in ANGLED:
            angles[i]=float(op.params[0])
    phase=float(circuit.global_phase)
    if not np.isfinite(angles).all() or not np.isfinite(phase):
        raise ValueError("nonfinite circuit parameters")
    return n,rows,angles,phase

class QuestProbe:
    """Single owner per process; no auto-fallback; CPU/OpenMP only."""
    def __init__(self,library,threads):
        global _USED
        with _LOCK:
            if _USED or threads not in (1,2,4,8):
                raise ValueError("one QuEST environment per process, 1/2/4/8 threads")
            self._lib=ct.CDLL(str(Path(library).resolve(strict=True)))
            self._lib.ketary_quest_init.argtypes=[ct.c_int]
            self._lib.ketary_quest_init.restype=ct.c_int
            self._lib.ketary_quest_close.argtypes=[]
            self._lib.ketary_quest_close.restype=ct.c_int
            self._lib.ketary_quest_run.argtypes=[ct.c_int,ct.c_int,_I,_D,_D,ct.c_double,_D,_D]
            self._lib.ketary_quest_run.restype=ct.c_int
            if self._lib.ketary_quest_init(int(threads>1)):
                raise RuntimeError("QuEST environment initialization failed")
            _USED=True
            self._closed=False

    def close(self):
        with _LOCK:
            if not self._closed:
                if self._lib.ketary_quest_close():
                    raise RuntimeError("QuEST finalization failed")
                self._closed=True

    def execute(self,program,state):
        n,rows,angles,phase=program
        if not 1<=n<=22 or rows.shape!=(len(angles),3) or len(rows)>100000:
            raise ValueError("invalid program payload")
        state=np.asarray(state,dtype=np.complex128,order="C")
        if state.shape!=(1<<n,) or not np.isfinite(state).all() or not np.isclose(
                np.vdot(state,state).real,1,rtol=0,atol=1e-9):
            raise ValueError("expected normalized complex state")
        output=np.empty_like(state)
        times=np.empty(3,dtype=np.float64)
        with _LOCK:
            if self._closed:
                raise RuntimeError("QuEST environment closed")
            status=self._lib.ketary_quest_run(n,len(rows),rows,angles,state.view(np.float64),
                                             phase,output.view(np.float64),times)
        if status:
            raise RuntimeError(f"QuEST bridge error {status}")
        return output,times
