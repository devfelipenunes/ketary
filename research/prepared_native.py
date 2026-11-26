"""Explicit bounded prepared programs; research only, not a public SDK API."""
from dataclasses import dataclass
import math
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from combined_native_benchmark import rust_pack

MAX_ROWS=256
MAX_OUTPUT=128*1024**2

def frozen(array,dtype,shape):
    return np.frombuffer(np.asarray(array,dtype=dtype,order="C").tobytes(),dtype=dtype).reshape(shape)

@dataclass(frozen=True)
class Prepared:
    n: int
    ops: np.ndarray
    angles: np.ndarray
    phase: float
    parameters: tuple
    slots: tuple

    def program(self):
        return self.n,self.ops,self.angles,self.phase

    def angle_table(self,values):
        if len(values)<1 or len(values)>MAX_ROWS or len(values)*(1<<self.n)*16>MAX_OUTPUT:
            raise ValueError("batch bounds exceeded")
        vals=np.asarray(values,dtype=np.float64)
        if vals.shape!=(len(values),len(self.parameters)) or not np.isfinite(vals).all():
            raise ValueError("expected finite ordered parameter rows")
        table=np.broadcast_to(self.angles,(len(vals),len(self.angles))).copy()
        for gate,column in self.slots:
            table[:,gate]=vals[:,column]
        return table

def prepare(circuit):
    if not isinstance(circuit,QuantumCircuit):
        raise TypeError("expected QuantumCircuit")
    if circuit.num_clbits or circuit.metadata or getattr(circuit,"layout",None) is not None:
        raise ValueError("unsupported native circuit annotations or classical bits")
    if not 1<=circuit.num_qubits<=22 or len(circuit.data)>100000:
        raise ValueError("unsupported width or count")
    if getattr(circuit.global_phase,"parameters",()):
        raise ValueError("symbolic phase unsupported")
    params=tuple(circuit.parameters)
    columns={p:i for i,p in enumerate(params)}
    slots=[]
    for index,entry in enumerate(circuit.data):
        for p in entry.operation.params:
            if getattr(p,"parameters",()):
                if not isinstance(p,Parameter) or entry.operation.name not in ("rx","ry","rz","p"):
                    raise ValueError("only direct angle parameters supported")
                slots.append((index,columns[p]))
    skeleton=circuit.assign_parameters({p:0. for p in params},inplace=False) if params else circuit
    n,ops,angles,phase=rust_pack(skeleton)
    return Prepared(n,frozen(ops,np.int32,ops.shape),frozen(angles,np.float64,angles.shape),
                    phase,params,tuple(slots))

def fuse(program):
    """Adjacent exact involutions and same-axis rotations only; no reordering."""
    if program.parameters:
        raise ValueError("bind first; symbolic fusion is not supported")
    out=[];angles=[]
    for raw,theta in zip(program.ops,program.angles,strict=True):
        row=tuple(map(int,raw));theta=float(theta)
        if out and row==out[-1]:
            if row[0] in (0,1,2,3,7,8,9):
                out.pop();angles.pop();continue
            if row[0] in (4,5,6,10):
                combined=angles[-1]+theta
                # Do not reduce modulo 2pi (spin rotations carry phase).
                if math.isfinite(combined) and max(abs(theta),abs(angles[-1]),abs(combined))<=1e4:
                    angles[-1]=combined;continue
        out.append(row);angles.append(theta)
    return Prepared(program.n,frozen(out,np.int32,(len(out),3)),
                    frozen(angles,np.float64,(len(out),)),program.phase,(),())
