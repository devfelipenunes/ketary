"""Round 7 B: de-duplicate equal post observables and avoid redundant witness work."""
from common5 import *
from engine import Report,SCOPE,valid_pauli,difference,product_witness,_add,Witness
from front_b import Session
from benchmark_engine import setup
from test_engine import native
def fast_witness(n,d,k):
    """A nonzero Pauli polynomial has a nonzero product-state expectation.
    Choose local axes supporting one nonzero monomial, then condition signs
    without eliminating the nonzero polynomial. All arithmetic exact.
    """
    if not d:raise ValueError("zero difference")
    x,z=next(iter(d))
    axes=tuple("IZXY"[2*((x>>i)&1)+((z>>i)&1)] if (x|z)&(1<<i) else "Z" for i in range(n))
    ax=sum((a in "XY")<<i for i,a in enumerate(axes))
    az=sum((a in "ZY")<<i for i,a in enumerate(axes))
    poly={}
    for (x,z),(a,b) in d.items():
        mask=x|z
        if ((x^ax)|(z^az))&mask:continue
        _add(poly,mask,a,b)
    assert poly
    signs=[]
    for i in range(n):
        if set(poly)=={0}:
            signs.extend([1]*(n-i));break
        bit=1<<i
        def reduce(s):
            out={}
            for mask,(a,b) in poly.items():
                mul=s if mask&bit else 1
                _add(out,mask&~bit,mul*a,mul*b)
            return out
        plus=reduce(1)
        if plus:signs.append(1);poly=plus
        else:signs.append(-1);poly=reduce(-1)
        assert poly
    assert set(poly)=={0}
    return Witness(axes,tuple(signs),poly[0],k)

def grouped(s,obs,backend,budget=2_000_000):
    if not isinstance(s,Session) or s.has_t or type(obs) is not tuple or not 1<=len(obs)<=256:raise ValueError("session")
    if type(budget) is not int or not 1<=budget<=2_000_000 or len(s.pre.gates)*len(obs)>budget:raise ValueError("budget")
    for ob in obs:
        if type(ob) is not Obligation:raise ValueError("obligation")
        valid_pauli(ob.pre,s.pre.width);valid_pauli(ob.post,s.pre.width)
    # Same conservative gate-visits cap as original session, regardless of reuse.
    unique=tuple(dict.fromkeys(ob.post for ob in obs));values={}
    for i in range(0,len(unique),64):
        p=unique[i:i+64];method="batch" if len(p)>=8 else "scalar"
        values.update(zip(p,backend.run(s.pre,p,method)))
    reports={};out=[]
    for ob in obs:
        if ob not in reports:
            x,z,r=values[ob.post];d=difference(((x,z,(-1)**r,0),),0,ob.pre)
            w=fast_witness(s.pre.width,d,0) if d else None
            reports[ob]=Report("FAIL" if d else "PASS","grouped",s.identity,digest({"pre":ob.pre,"post":ob.post}),SCOPE,"nonzero exact product-state expectation" if d else "exact coefficient equality",w)
        out.append(reports[ob])
    return tuple(out)
def main():
    rng=random.Random(91);backend=native();rows=[];checks=0
    # Compare exact witness object, not merely status.
    for n in (2,16,32,64):
        for _ in range(100):
            d={}
            for j in range(rng.randrange(1,20)):
                _add(d,(rng.getrandbits(n),rng.getrandbits(n)),rng.randrange(-10,11),rng.randrange(-10,11))
            if d:assert fast_witness(n,d,4)==product_witness(n,d,4)
    for n in (16,32,64):
        for g in (100,10000):
            c,p,base=setup(n,g,64);s=Session(p)
            for m in (1,8,64):
                for unique in sorted({1,m}):
                    obs=tuple(base[i%unique] for i in range(m))
                    old=lambda:s.run(obs,native=backend)
                    new=lambda:grouped(s,obs,backend)
                    assert semantic(old())==semantic(new());checks+=m
                    rows.append({"n":n,"gates":g,"m":m,"unique":unique,"timings":measure({"session":old,"grouped":new})})
    output({"scope":"Clifford session report parity; immutable report sharing, same original work cap, no persistent cache; duplicate workload distinct from unique workload","report_checks":checks,"rows":rows})
if __name__=="__main__":main()
