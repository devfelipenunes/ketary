"""Research-only syntax candidates. Same exact Pauli transition, no public API."""
from dataclasses import dataclass
from native9 import RustSession
from engine import Obligation,valid_pauli
from subspace10 import clean

def label_mask(label,n):
    if type(label) is not str:raise TypeError("Pauli label")
    r=int(label.startswith("-"))
    if r:label=label[1:]
    if len(label)!=n or any(c not in "IXYZ" for c in label):raise ValueError("full Pauli label, highest wire first")
    x=sum((c in "XY")<<i for i,c in enumerate(reversed(label)))
    z=sum((c in "ZY")<<i for i,c in enumerate(reversed(label)))
    return x,z,r

@dataclass(frozen=True)
class On:
    wire:int
    axis:str
@dataclass(frozen=True)
class Product:
    factors:tuple
    negative:bool=False
    def mask(self,n):
        if type(self.factors) is not tuple or type(self.negative) is not bool:raise ValueError("product")
        x=z=0;seen=set()
        for f in self.factors:
            if type(f) is not On or type(f.wire) is not int or not 0<=f.wire<n or type(f.axis) is not str or f.axis not in ("X","Y","Z") or f.wire in seen:raise ValueError("factor must use distinct in-range wire")
            seen.add(f.wire);x|=(f.axis in "XY")<<f.wire;z|=(f.axis in "ZY")<<f.wire
        return x,z,int(self.negative)
def spec(p,n):
    if type(p) is Product:return p.mask(n)
    if type(p) is str:return label_mask(p,n)
    valid_pauli(p,n);return p
@dataclass(frozen=True)
class Transition:
    pre:object
    post:object
    def obligation(self,n):return Obligation(spec(self.pre,n),spec(self.post,n))
    def verify(self,circuit):
        return LabSession.prepare(circuit).verify(self)
@dataclass(frozen=True)
class Ensures:
    pre:object
    def ensures(self,post):return Transition(self.pre,post)
def requires(pre):return Ensures(pre)
@dataclass(frozen=True)
class CleanAncillas:
    wires:tuple
    def verify(self,circuit):return LabSession.prepare(circuit).verify(self)
@dataclass(frozen=True)
class LabSession:
    engine:RustSession
    @classmethod
    def prepare(cls,circuit):return cls(RustSession.from_circuit(circuit))
    def verify(self,contract,*,max_terms=4096,max_work=2_000_000):
        if type(contract) is Transition:return self.engine.verify((contract.obligation(self.engine.width),),max_terms=max_terms,max_work=max_work)[0]
        if type(contract) is CleanAncillas:return clean(self.engine,contract.wires,max_terms=max_terms,max_work=max_work)
        raise TypeError("explicit transition or clean-ancilla contract required")
