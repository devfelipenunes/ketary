"""B: explicit immutable session; amortize admission without public cache."""
from dataclasses import dataclass,field
from common5 import *
from engine import _verify_admitted
from benchmark_engine import setup
from test_engine import native

@dataclass(frozen=True)
class Session:
    pre:Prepared
    identity:str=field(init=False)
    has_t:bool=field(init=False)
    def __post_init__(self):
        object.__setattr__(self,"identity",admission(self.pre))
        object.__setattr__(self,"has_t",any(g[0]>=6 for g in self.pre.gates))
    def run(self,obs,*,native=None,max_work=2_000_000):
        if type(obs) is not tuple or not 1<=len(obs)<=256:raise ValueError("request count")
        if type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("budget")
        # No enlarged sparse budget: only batch Clifford in this experiment.
        if self.has_t:raise ValueError("session batch Clifford only")
        if len(self.pre.gates)*len(obs)>max_work:raise ValueError("aggregate budget")
        out=[]
        for i in range(0,len(obs),64):
            part=obs[i:i+64]
            out.extend(_verify_admitted(self.pre,self.identity,False,part,native=native,max_work=max(1,len(self.pre.gates)*len(part))))
        return tuple(out)

def main():
    backend=native();rows=[];checks=0
    for n in (16,32):
        for g in (100,1000,10000):
            c,p,base=setup(n,g,64);session=Session(p)
            for m in (1,8,64,256):
                if g*m>2_000_000:continue
                obs=(base*4)[:m]
                def old():return tuple(r for i in range(0,m,64) for r in verify(p,obs[i:i+64],native=backend))
                def new():return session.run(obs,native=backend)
                assert semantic(old())==semantic(new());checks+=m
                rows.append({"n":n,"gates":g,"m":m,"timings":measure({"legacy_chunks":old,"session_reuse":new,"session_create_run":lambda:Session(p).run(obs,native=backend)})})
            c.z(0);assert session.identity!=Session(prepare(c)).identity
    try:Session(p).run((base*4),native=backend,max_work=1)
    except ValueError:pass
    else:raise AssertionError("aggregate limit")
    output({"scope":"Clifford transition reports, repeated obligations allowed; immutable in-process research session only; explicit setup; native buffers still copied","checks":checks,"rows":rows})
if __name__=="__main__":main()
