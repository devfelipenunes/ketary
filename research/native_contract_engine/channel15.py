"""Bounded numerical channel-effect contracts, separate from exact Rust proofs."""
from dataclasses import dataclass
import numpy as np
from qiskit.quantum_info import Kraus,SuperOp

@dataclass(frozen=True)
class EffectReport:
    status:str
    scope:str
    residual:float
    witness:tuple|None
    replay_gap:float|None
    tolerance:float
    def require(self):
        if self.status!="PASS":raise AssertionError(self.status+": "+self.scope)
        return self

def admit(a,b,ks):
    if type(a) is not np.ndarray or type(b) is not np.ndarray or a.ndim!=2 or a.shape!=b.shape or a.shape[0]!=a.shape[1] or a.shape[0] not in (2,4,8,16) or type(ks) is not tuple or not 1<=len(ks)<=16:raise ValueError("bounded ndarray effects and Kraus tuple")
    if any(type(k) is not np.ndarray or k.shape!=a.shape for k in ks):raise ValueError("Kraus shape")
    a,b=np.array(a,complex,copy=True),np.array(b,complex,copy=True)
    ks=tuple(np.array(k,complex,copy=True) for k in ks)
    for m in (a,b):
        if not np.isfinite(m).all() or np.linalg.norm(m-m.conj().T,2)>1e-12:raise ValueError("Hermitian effect")
        vals=np.linalg.eigvalsh(m)
        if vals[0]<-1e-12 or vals[-1]>1+1e-12:raise ValueError("effect range")
    if any(not np.isfinite(k).all() for k in ks) or np.linalg.norm(sum(k.conj().T@k for k in ks)-np.eye(len(a)),2)>1e-12:raise ValueError("CPTP")
    return a,b,ks

@dataclass(frozen=True)
class ChannelEffect:
    tolerance:float=1e-9
    def verify(self,a,b,ks,*,method="kraus"):
        if type(self.tolerance) not in (float,int) or not 1e-11<=self.tolerance<=1e-6 or method not in ("kraus","superop"):raise ValueError("policy")
        a,b,ks=admit(a,b,ks)
        if method=="kraus":adj=sum(k.conj().T@b@k for k in ks)
        else:adj=(SuperOp(Kraus(list(ks))).data.conj().T@b.reshape(-1,order="F")).reshape(b.shape,order="F")
        d=a-adj;vals,vec=np.linalg.eigh((d+d.conj().T)/2);v=vec[:,-1];res=float(vals[-1])
        rho=np.outer(v,v.conj());out=sum(k@rho@k.conj().T for k in ks);gap=float(np.trace(a@rho-b@out).real)
        if abs(gap-res)>1e-10:raise ArithmeticError("replay")
        guard=max(1e-12,8*float(np.linalg.norm(d@v-res*v)),8*float(np.linalg.norm(d-d.conj().T,2)),8*float(np.linalg.norm(sum(k.conj().T@k for k in ks)-np.eye(len(a)),2)))
        status="PASS" if res<self.tolerance-guard else "FAIL" if res>self.tolerance+guard and gap>self.tolerance+guard else "INCONCLUSIVE"
        return EffectReport(status,"Numerical all-state effect inequality A <= E†(B) + epsilon I; diagnostic rounding guard, not exact proof",res,tuple(complex(x) for x in v) if status=="FAIL" else None,gap if status=="FAIL" else None,self.tolerance)
