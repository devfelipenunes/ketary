"""Research exact clean-subspace contracts using compiled Clifford+T propagation."""
from dataclasses import dataclass
from native9 import RustSession,bounds
from engine import _add,product_witness,Witness
from sparse import BudgetExceeded

@dataclass(frozen=True)
class CleanReport:
    status:str
    circuit_id:str
    wires:tuple
    reason:str
    witness:Witness|None=None

def clean(s,w,*,max_terms=4096,max_work=2_000_000):
    if type(s) is not RustSession or type(w) is not tuple or not w or len(w)>s.width or any(type(i) is not int or not 0<=i<s.width for i in w) or len(set(w))!=len(w):raise ValueError("ancilla wires")
    bounds(max_terms,max_work)
    mask=sum(1<<i for i in w);remaining=max_work
    for i in w:
        if remaining<=0:return CleanReport("INCONCLUSIVE",s.identity,w,"shared work budget")
        try:r=s.propagate((0,1<<i,0),max_terms=max_terms,max_work=remaining)
        except BudgetExceeded:return CleanReport("INCONCLUSIVE",s.identity,w,"propagation budget")
        remaining-=r.work
        # P U† Z_i U P restricted to P: X/Y on clean ancillas vanish;
        # Z on clean ancillas is +1. Compare reduced operator to identity.
        d={}
        for x,z,a,b in r.terms:
            if not x&mask:_add(d,(x,z&~mask),a,b)
        _add(d,(0,0),-(1<<r.denominator_power),0)
        if d:
            witness=product_witness(s.width,d,r.denominator_power)
            assert all(witness.axes[j]=="Z" and witness.signs[j]==1 for j in w)
            return CleanReport("FAIL",s.identity,w,f"clean subspace violated on wire {i}",witness)
    return CleanReport("PASS",s.identity,w,"all projected Z generators equal identity")
