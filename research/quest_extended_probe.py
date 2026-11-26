"""Experimental extended native gate bridge; no public SDK or fallback."""
import ctypes as ct
from pathlib import Path
from threading import Lock
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import (HGate,XGate,YGate,ZGate,RXGate,RYGate,RZGate,CXGate,CZGate,
    SwapGate,PhaseGate,CPhaseGate,RZZGate,CCXGate,MCXGate)
import _ketary_capi_probe as capi
from ketary._result import Result

NAMES=("h","x","y","z","rx","ry","rz","cx","cz","swap","p","cp","rzz","ccx","mcx")
TYPES=(HGate,XGate,YGate,ZGate,RXGate,RYGate,RZGate,CXGate,CZGate,SwapGate,PhaseGate,
       CPhaseGate,RZZGate,CCXGate,MCXGate)
OPS={name:i for i,name in enumerate(NAMES)}
ANGLED={4,5,6,10,11,12}
CONTROLLED={7,8,11,13,14}
_I=np.ctypeslib.ndpointer(dtype=np.int32,ndim=2,flags="C_CONTIGUOUS")
_D=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags="C_CONTIGUOUS")
_LOCK=Lock()
_USED=False

def check_mode(c):
    if not isinstance(c,QuantumCircuit):raise TypeError("expected QuantumCircuit")
    if not 1<=c.num_qubits<=22 or len(c.data)>100000 or c.num_clbits or c.parameters or c.metadata or getattr(c,"layout",None) is not None:
        raise ValueError("unsupported mode, metadata, layout or bounds")

def python_pack(c):
    check_mode(c)
    rows=np.full((len(c.data),24),-1,dtype=np.int32);angles=np.zeros(len(rows))
    for i,entry in enumerate(c.data):
        op=entry.operation;kind=OPS.get(op.name,-1)
        if kind<0 or op.base_class is not TYPES[kind] or entry.clbits:
            raise ValueError("unsupported operation")
        wires=[c.find_bit(q).index for q in entry.qubits]
        k=len(wires)
        expected=3 if kind==13 else 2 if kind in (7,8,9,11,12) else 1
        if (not 3<=k<=c.num_qubits if kind==14 else k!=expected) or len(set(wires))!=k:
            raise ValueError("invalid arity")
        if kind in CONTROLLED and op.ctrl_state!=(1<<op.num_ctrl_qubits)-1:
            raise ValueError("open control unsupported")
        if len(op.params)!=int(kind in ANGLED):raise ValueError("invalid parameters")
        rows[i,0:2]=kind,k;rows[i,2:2+k]=wires
        if kind in ANGLED:angles[i]=float(op.params[0])
    phase=float(c.global_phase)
    if not np.isfinite(angles).all() or not np.isfinite(phase):raise ValueError("nonfinite angle or phase")
    return c.num_qubits,rows,angles,phase

def rust_pack(c):
    check_mode(c)
    n,raw,theta,phase=capi.pack_extended(c._data)
    return n,np.frombuffer(raw,dtype=np.int32).reshape(-1,24),np.frombuffer(theta,dtype=np.float64),phase

def freeze(program):
    n,rows,angles,phase=program
    return n,np.frombuffer(rows.tobytes(),dtype=np.int32).reshape(-1,24),np.frombuffer(angles.tobytes(),dtype=np.float64),phase

class Extended:
    def __init__(self,library):
        global _USED
        with _LOCK:
            if _USED:raise RuntimeError("one environment per process")
            self.lib=ct.CDLL(str(Path(library).resolve(strict=True)))
            self.lib.extended_init.argtypes=[];self.lib.extended_init.restype=ct.c_int
            self.lib.extended_close.argtypes=[];self.lib.extended_close.restype=ct.c_int
            self.lib.extended_run.argtypes=[ct.c_int,ct.c_int,ct.c_int,_I,_D,_D,ct.c_double,_D,_D]
            self.lib.extended_run.restype=ct.c_int
            if self.lib.extended_init():raise RuntimeError("native initialization failed")
            _USED=True;self.closed=False

    def close(self):
        with _LOCK:
            if not self.closed:
                if self.lib.extended_close():raise RuntimeError("native close failed")
                self.closed=True

    def run(self,program,state,angle_rows=None):
        n,ops,angles,phase=program
        if type(n) is not int or not 1<=n<=22 or ops.shape!=(len(angles),24) or len(angles)>100000 or ops.dtype!=np.int32 or not ops.flags.c_contiguous:
            raise ValueError("invalid program")
        if angle_rows is None:angle_rows=angles.reshape(1,-1)
        count=len(angle_rows)
        if not 1<=count<=256 or count*(1<<n)*16>128*1024**2 or count*len(angles)*8>64*1024**2:
            raise ValueError("batch bounds")
        table=np.asarray(angle_rows,dtype=np.float64,order="C")
        if table.shape!=(count,len(angles)) or not np.isfinite(table).all() or not np.isfinite(phase):raise ValueError("invalid angles")
        v=np.asarray(state,dtype=np.complex128,order="C")
        if v.shape!=(1<<n,) or not np.isfinite(v).all() or not np.isclose(np.vdot(v,v).real,1,rtol=0,atol=1e-9):
            raise ValueError("invalid normalized state")
        # A single-run output owns its allocation (no row view).
        out=np.empty(1<<n if count==1 else (count,1<<n),dtype=np.complex128)
        t=np.empty(5)
        with _LOCK:
            if self.closed:raise RuntimeError("closed")
            rc=self.lib.extended_run(n,len(ops),count,ops,table.reshape(-1),v.view(np.float64),
                                     phase,out.view(np.float64).reshape(-1),t)
        if rc:raise RuntimeError(f"extended bridge rejected payload: {rc}")
        return out,t

    def snapshot(self,program,state):
        # Fresh exclusive native output; public Result still returns defensive copies.
        return Result._from_evolution(self.run(program,state)[0])
