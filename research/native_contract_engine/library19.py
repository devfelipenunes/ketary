"""Typed, circuit-bound component library. No mutable global registry."""
from dataclasses import dataclass
from planner19 import independent_image, snapshot_id, multiply
from engine import valid_pauli

def signed_product(a,b):
    def lift(p):
        x,z,s=p;return x,z,((x&z).bit_count()+2*s)%4
    x,z,k=multiply(lift(a),lift(b))
    phase=(k-(x&z).bit_count())%4
    if phase not in (0,2):raise ValueError("non-Hermitian product")
    return x,z,phase//2

@dataclass(frozen=True)
class Component:
    name:str
    width:int
    circuit_id:str
    pre:tuple
    post:tuple

@dataclass(frozen=True)
class Library:
    entries:tuple=()
    def add(self,name,n,packed,pre,post):
        if type(name) is not str or not 1<=len(name)<=80 or not name.isascii() or any(c.name==name for c in self.entries) or len(self.entries)>=64:
            raise ValueError("component name/count")
        valid_pauli(pre,n)
        if independent_image(n,packed,post)!=pre:
            raise ValueError("component not independently verified in Clifford scope")
        c=Component(name,n,snapshot_id(n,packed),pre,post)
        return Library(self.entries+(c,))
    def get(self,name):
        for c in self.entries:
            if c.name==name:return c
        raise KeyError(name)
    def product(self,name_a,name_b,n,packed):
        """Recheck sources against caller-supplied bytes; do not trust a report.
        Multiplication of two verified conjugation identities yields a third
        when both products are Hermitian. No subspace or phase-sensitive reuse.
        """
        a,b=self.get(name_a),self.get(name_b)
        if any(c.width!=n or c.circuit_id!=snapshot_id(n,packed) or independent_image(n,packed,c.post)!=c.pre for c in (a,b)):
            raise ValueError("source identity or guarantee mismatch")
        return signed_product(a.pre,b.pre),signed_product(a.post,b.post)
