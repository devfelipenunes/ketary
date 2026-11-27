"""Numeric CPTP effect verification: matched Kraus vs SuperOp adjoints."""
from common5 import *
from qiskit.quantum_info import Kraus,SuperOp
def admit(a,b,ks):
    a=np.array(a,complex,copy=True);b=np.array(b,complex,copy=True)
    if a.ndim!=2 or a.shape!=b.shape or a.shape[0]!=a.shape[1] or len(a) not in (2,4,8,16) or type(ks) not in (tuple,list) or not 1<=len(ks)<=16:raise ValueError("shape")
    ks=tuple(np.array(k,complex,copy=True) for k in ks);d=len(a)
    for m in (a,b):
        if not np.isfinite(m).all() or np.linalg.norm(m-m.conj().T,2)>1e-12:raise ValueError("effect")
        v=np.linalg.eigvalsh(m)
        if v[0]<-1e-12 or v[-1]>1+1e-12:raise ValueError("range")
    if any(k.shape!=a.shape or not np.isfinite(k).all() for k in ks):raise ValueError("Kraus")
    if np.linalg.norm(sum(k.conj().T@k for k in ks)-np.eye(d),2)>1e-12:raise ValueError("not TP")
    return a,b,ks
def finish(a,adj,ks,b,tol=1e-9):
    m=a-adj;v,e=np.linalg.eigh((m+m.conj().T)/2);w=e[:,-1];res=float(v[-1])
    rho=np.outer(w,w.conj());out=sum(k@rho@k.conj().T for k in ks)
    gap=float(np.trace(a@rho-b@out).real)
    assert abs(gap-res)<1e-10
    return ("PASS" if res<tol-1e-12 else "FAIL" if res>tol+1e-12 and gap>tol+1e-12 else "INCONCLUSIVE",res,gap)
def route(a,b,ks,method):
    a,b,ks=admit(a,b,ks)
    if method=="kraus":adj=sum(k.conj().T@b@k for k in ks)
    else:adj=(SuperOp(Kraus(list(ks))).data.conj().T@b.reshape(-1,order="F")).reshape(b.shape,order="F")
    return finish(a,adj,ks,b)
def main():
    rows=[];checks=0
    for n in (1,2,3,4):
        d=1<<n;id=np.eye(d);z=np.diag([(-1)**(i&1) for i in range(d)]);x=np.kron(np.eye(d//2),np.array([[0,1],[1,0]]));p=(id+x)/2
        for rate in (0.,.01,.25):
            for kind in ("dephase","damp"):
                if kind=="dephase":ks=(np.sqrt(1-rate)*id,np.sqrt(rate)*z)
                else:ks=(np.kron(np.eye(d//2),np.diag([1,np.sqrt(1-rate)])),np.kron(np.eye(d//2),np.array([[0,np.sqrt(rate)],[0,0]])))
                a=p;b=p
                r=route(a,b,ks,"kraus");s=route(a,b,ks,"superop");assert r[0]==s[0] and abs(r[1]-s[1])<1e-10
                expect=0. if rate==0 else rate if kind=="dephase" else (1-np.sqrt(1-rate))/2
                assert abs(r[1]-expect)<1e-10;assert r[0]==("PASS" if rate==0 else "FAIL");checks+=1
                rows.append({"n":n,"kind":kind,"rate":rate,"status":r[0],"residual":r[1],"timings":measure({"kraus":lambda:route(a,b,ks,"kraus"),"superop":lambda:route(a,b,ks,"superop")})})
    try:route(np.eye(2),np.eye(2),(np.eye(2)*.9,),"kraus")
    except ValueError:pass
    else:raise AssertionError("non-TP")
    output({"scope":"bounded numeric effect inequality for CPTP, max spectral residual and independent forward density witness; not hardware or channel equivalence, diagnostic tolerance","checks":checks,"rows":rows})
if __name__=="__main__":main()
