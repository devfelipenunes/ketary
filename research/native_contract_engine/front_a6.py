"""Research: typed joint subspace planner; exact and probability scopes separate."""
from dataclasses import dataclass
from common5 import *
from front_a import exact,numerical
from qiskit import QuantumCircuit
import ketary as q
@dataclass(frozen=True)
class Clean:
    wires:tuple
    metric:str="exact"
    tolerance:float|None=None
def check(c,ob):
    if type(ob) is not Clean:raise TypeError("obligation")
    if ob.metric=="exact":
        if ob.tolerance is not None:raise ValueError("exact has no tolerance")
        try:p=prepare(c,allow_t=True)
        except (ValueError,TypeError):
            from front_a import SubspaceReport
            return SubspaceReport("UNSUPPORTED","exact",ob.wires,"exact zero leakage",None,None)
        return exact(p,ob.wires)
    if ob.metric=="probability" and ob.tolerance is not None:return numerical(c,ob.wires,ob.tolerance)
    raise ValueError("metric")
def main():
    rows=[]
    for n in (3,5,6):
        for w in ((0,),(0,n-1)):
            for kind in ("clean","swap","dirty","tiny","boundary","outside"):
                qc=QuantumCircuit(n)
                if kind=="swap":qc.swap(0,n-1)
                if kind=="dirty":qc.x(0)
                if kind in ("tiny","boundary"):qc.ry(2*np.arcsin(np.sqrt(1e-12 if kind=="tiny" else 1e-9)),0)
                if kind=="outside":qc.h(1)
                # SWAP is decomposed explicitly into the admitted Clifford gates.
                if kind=="swap":
                    qc=QuantumCircuit(n);qc.cx(0,n-1);qc.cx(n-1,0);qc.cx(0,n-1)
                c=q.from_qiskit(qc)
                x=check(c,Clean(w));y=check(c,Clean(w,"probability",1e-9))
                expected="FAIL" if kind=="dirty" or (kind=="swap" and len(w)==1) else "UNSUPPORTED" if kind in ("tiny","boundary") else "PASS"
                assert x.status==expected,(n,w,kind,x)
                assert y.status==("INCONCLUSIVE" if kind=="boundary" else "FAIL" if expected=="FAIL" else "PASS"),(n,w,kind,y)
                rows.append({"n":n,"wires":w,"kind":kind,"exact":x.status,"probability":y.status})
    output({"scope":"joint clean ancilla; no silent numerical fallback","checks":len(rows)*2,"rows":rows})
if __name__=="__main__":main()
