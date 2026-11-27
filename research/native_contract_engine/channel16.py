"""Numerical sequential CPTP effect verification without Kraus-product expansion."""
from dataclasses import dataclass
import numpy as np
from qiskit.quantum_info import Kraus,SuperOp
from channel15 import admit,EffectReport
@dataclass(frozen=True)
class SequentialEffect:
    tolerance:float=1e-9
    def verify(self,a,b,stages,*,method="kraus"):
        if type(self.tolerance) not in (int,float) or not 1e-11<=self.tolerance<=1e-6 or type(stages) is not tuple or not 1<=len(stages)<=16 or method not in ("kraus","superop"):raise ValueError("policy")
        prepared=[]
        for ks in stages:
            aa,bb,kk=admit(a,b,ks);prepared.append(kk)
        adj=bb
        for ks in reversed(prepared):
            if method=="kraus":adj=sum(k.conj().T@adj@k for k in ks)
            else:adj=(SuperOp(Kraus(list(ks))).data.conj().T@adj.reshape(-1,order="F")).reshape(bb.shape,order="F")
        d=aa-adj;vals,vec=np.linalg.eigh((d+d.conj().T)/2);v=vec[:,-1];res=float(vals[-1])
        rho=np.outer(v,v.conj());out=rho
        for ks in prepared:out=sum(k@out@k.conj().T for k in ks)
        gap=float(np.trace(aa@rho-bb@out).real)
        tp=sum(float(np.linalg.norm(sum(k.conj().T@k for k in ks)-np.eye(len(aa)),2)) for ks in prepared)
        guard=max(1e-12*len(stages),8*float(np.linalg.norm(d@v-res*v)),8*float(np.linalg.norm(d-d.conj().T,2)),8*tp,8*abs(gap-res))
        status="PASS" if res<self.tolerance-guard else "FAIL" if res>self.tolerance+guard and gap>self.tolerance+guard else "INCONCLUSIVE"
        return EffectReport(status,"Numerical sequential CPTP all-state effect inequality, no certified roundoff",res,tuple(complex(x) for x in v) if status=="FAIL" else None,gap if status=="FAIL" else None,self.tolerance)
