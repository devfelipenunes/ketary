"""F: versioned compact Clifford snapshot, one packed representation and binary identity."""
from dataclasses import dataclass,field
import hashlib,struct
from common5 import *
from engine import Report,SCOPE,valid_pauli,difference,product_witness
from round3 import CLASSES,CODES
from front_b import Session
from benchmark_engine import setup
from test_engine import native
import ketary as q

IDENTITY=b"ketary-research/pauli-clifford-packed/v2\0"
def packed_id(n,data):
    if type(n) is not int or not 1<=n<=64 or type(data) is not bytes or len(data)%3 or len(data)>300_000:raise ValueError("shape")
    a=np.frombuffer(data,dtype=np.uint8).reshape(-1,3);op,x,y=a.T
    if np.any(op>5) or np.any(x>=n) or np.any((op==5)&((y>=n)|(x==y))) or np.any((op!=5)&(y!=0)):raise ValueError("gate")
    return hashlib.sha256(IDENTITY+struct.pack(">BI",n,len(data)//3)+data).hexdigest()
@dataclass(frozen=True)
class Compact:
    width:int
    packed:bytes
    identity:str=field(init=False)
    def __post_init__(self):object.__setattr__(self,"identity",packed_id(self.width,self.packed))

def compact(c):
    if not isinstance(c,q.Circuit):raise TypeError("Ketary Circuit")
    qc=c.to_qiskit()
    if not 1<=qc.num_qubits<=64 or qc.num_clbits or qc.num_parameters or len(qc.data)>100_000:raise ValueError("circuit")
    w={b:i for i,b in enumerate(qc.qubits)};buf=bytearray()
    for inst in qc.data:
        op=inst.operation;i=CODES.get(op.base_class)
        if i is None or i>5 or inst.clbits or op.params or getattr(op,"condition",None) is not None:raise ValueError("gate")
        if len(inst.qubits)!=(2 if i==5 else 1) or (i==5 and op.ctrl_state!=1):raise ValueError("arity/control")
        a=w[inst.qubits[0]];b=w[inst.qubits[1]] if i==5 else 0
        buf.extend((i,a,b))
    return Compact(qc.num_qubits,bytes(buf))

def run(p,obs,backend,budget=2_000_000):
    if type(p) is not Compact or type(obs) is not tuple or not 1<=len(obs)<=64 or type(budget) is not int or not 1<=budget<=2_000_000:raise ValueError("request")
    if len(p.packed)//3*len(obs)>budget:raise ValueError("budget")
    for ob in obs:
        if type(ob) is not Obligation:raise ValueError("obligation")
        valid_pauli(ob.pre,p.width);valid_pauli(ob.post,p.width)
    ps=[o.post for o in obs];out=[]
    for ob,(x,z,r) in zip(obs,backend.run(p,ps,"batch" if len(ps)>=8 else "scalar")):
        d=difference(((x,z,(-1)**r,0),),0,ob.pre)
        out.append(Report("FAIL" if d else "PASS","compact-v2",p.identity,digest({"pre":ob.pre,"post":ob.post}),SCOPE,"nonzero exact product-state expectation" if d else "exact coefficient equality",product_witness(p.width,d,0) if d else None))
    return tuple(out)
def project(rs):return [(r.status,r.obligation_id,r.scope,r.witness) for r in rs]
def main():
    backend=native();rows=[];checks=0
    for n in (16,32,64):
        for g in (100,10000):
            c,p,obs=setup(n,g,64);new=compact(c);old=Session(p)
            assert new.packed==p.packed and new.width==p.width and new.identity==packed_id(p.width,p.packed)
            for m in (1,8,64):
                o=obs[:m];assert project(old.run(o,native=backend))==project(run(new,o,backend));checks+=m
                routes={"legacy_admission":lambda:admission(p),"binary_admission":lambda:packed_id(p.width,p.packed),"legacy_cold":lambda:Session(prepare(c)).run(o,native=backend),"compact_cold":lambda:run(compact(c),o,backend),"legacy_warm":lambda:old.run(o,native=backend),"compact_warm":lambda:run(new,o,backend)}
                rows.append({"n":n,"gates":g,"m":m,"timings":measure(routes,reps=7)})
            c.z(0);assert compact(c).identity!=new.identity
    rejected=0
    for n,b in ((0,b""),(65,b""),(2,b"x"),(2,bytes((6,0,0))),(2,bytes((5,0,0))),(2,bytes((0,2,0))),(2,bytes((0,0,1)))):
        try:Compact(n,b)
        except ValueError:rejected+=1
        else:raise AssertionError("invalid packed input")
    output({"scope":"explicit research v2 binary identity is not backward compatible with v1 JSON hash; report semantic parity except circuit_id and method; admitted Clifford only, no sparse runtime integration or security boundary","checks":checks,"rejections":rejected,"rows":rows})
if __name__=="__main__":main()
