"""Exact rational Pauli-mixture transition contract, no float rounding."""
from dataclasses import dataclass
from fractions import Fraction
from facade17 import signed
from engine import product_witness,valid_pauli
from consolidated12 import Engine
from native9 import bounds
from sparse import BudgetExceeded

@dataclass(frozen=True)
class PauliNoise:
    # Entries: (signed Pauli representation, integer weight); signs do not
    # affect conjugation. All weights form a probability distribution.
    entries:tuple
    denominator:int
    def admitted(self,n):
        if type(self.entries) is not tuple or not 1<=len(self.entries)<=16 or type(self.denominator) is not int or not 1<=self.denominator<=65536:raise ValueError("noise bounds")
        out=[]
        for e in self.entries:
            if type(e) is not tuple or len(e)!=2 or type(e[1]) is not int or not 0<=e[1]<=self.denominator:raise ValueError("weight")
            out.append((signed(e[0],n),e[1]))
        if sum(w for _,w in out)!=self.denominator:raise ValueError("probability mass")
        return tuple(out)
@dataclass(frozen=True)
class RationalWitness:
    axes:tuple
    signs:tuple
    numerator:int
    denominator:int
@dataclass(frozen=True)
class NoiseReport:
    status:str
    scope:str
    coefficient:tuple|None
    image:tuple|None
    witness:RationalWitness|None
    work:int
    reason:str
    def require(self):
        if self.status!="PASS":raise AssertionError(self.reason)
        return self

@dataclass(frozen=True)
class NoiseTransition:
    pre:object
    post:object
    coefficient:Fraction=Fraction(1)
    def verify(self,n,stages,*,max_work=2_000_000):
        bounds(4096,max_work)
        if type(n) is not int or not 1<=n<=64 or type(stages) is not tuple or not 1<=len(stages)<=16 or type(self.coefficient) is not Fraction or abs(self.coefficient)>1 or self.coefficient.denominator.bit_length()>257:raise ValueError("request")
        pre,post=signed(self.pre,n),signed(self.post,n);prepared=[]
        for s in stages:
            if type(s) is PauliNoise:prepared.append((s,s.admitted(n)))
            elif type(s) is Engine and s.session.width==n and not any(s.session.packed[i]>=6 for i in range(0,len(s.session.packed),3)):prepared.append((s,None))
            else:raise ValueError("only exact Pauli mixtures and admitted Clifford unitary stages")
        scope="Exact rational equality E†(post)=coefficient*pre for ordered Clifford/Pauli-mixture channels, all input states"
        remaining=max_work;coef=Fraction((-1)**post[2]);p=(post[0],post[1],0)
        for s,entries in reversed(prepared):
            cost=len(entries) if entries is not None else max(1,3*len(s.session.packed)//3)
            if cost>=remaining:return NoiseReport("INCONCLUSIVE",scope,None,None,None,max_work,"stage work cap")
            remaining-=cost
            if entries is not None:
                factor=sum(w*(-1 if ((x&p[1])^(z&p[0])).bit_count()%2 else 1) for (x,z,_),w in entries)
                coef*=Fraction(factor,s.denominator)
            else:
                try:r=s.session.propagate(p,max_work=remaining)
                except BudgetExceeded:return NoiseReport("INCONCLUSIVE",scope,None,None,None,max_work,"propagation budget")
                assert r.denominator_power==0 and len(r.terms)==1
                x,z,a,b=r.terms[0];assert b==0 and abs(a)==1
                p=(x,z,0);coef*=a;remaining-=r.work
        target=self.coefficient*((-1)**pre[2])
        den=coef.denominator*target.denominator
        d={}
        for key,a in ((p[:2],coef), (pre[:2],-target)):
            value=d.get(key,(0,0))[0]+int(a*den)
            if value:d[key]=(value,0)
            else:d.pop(key,None)
        w=None
        if d:
            r=product_witness(n,d,0);v=Fraction(r.numerator[0],den);w=RationalWitness(r.axes,r.signs,v.numerator,v.denominator)
        return NoiseReport("FAIL" if d else "PASS",scope,(coef.numerator,coef.denominator),p,w,max_work-remaining,"exact coefficient mismatch" if d else "exact equality")
