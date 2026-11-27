"""Private research adapter. Real Ketary Circuit, exact transition scope only."""
from dataclasses import dataclass,field,asdict
import hashlib,struct
import ketary_native_research as rn
from round3 import CODES
from engine import Obligation,Report,Witness,SCOPE,valid_pauli,digest
from sparse import Propagation,BudgetExceeded
# Keep verification independent of benchmark-only platform modules.
def reduce_cone(packed,post):
    inv=(0,2,1,3,4,5,7,6)
    stack=[]
    for i in range(0,len(packed),3):
        op,a,b=packed[i:i+3]
        if stack and stack[-1]==(inv[op],a,b):stack.pop()
        else:stack.append((op,a,b))
    support=post[0]|post[1];kept=[]
    for op,a,b in reversed(stack):
        wires=(1<<a)|((1<<b) if op==5 else 0)
        if support&wires:kept.append((op,a,b));support|=wires
    return bytes(v for row in reversed(kept) for v in row)

ID=b"ketary-research/pauli-packed/v3\0"
@dataclass(frozen=True)
class RustSession:
    width:int
    packed:bytes
    identity:str=field(init=False)
    native:object=field(init=False,repr=False,compare=False)
    def __post_init__(self):
        if type(self.width) is not int or not 1<=self.width<=64 or type(self.packed) is not bytes or len(self.packed)>300_000 or len(self.packed)%3:raise ValueError("snapshot")
        object.__setattr__(self,"native",rn.PackedCircuit(self.width,self.packed))
        object.__setattr__(self,"identity",hashlib.sha256(ID+struct.pack(">BI",self.width,len(self.packed)//3)+self.packed).hexdigest())
    @classmethod
    def from_circuit(cls,c):
        import ketary as q
        if not isinstance(c,q.Circuit):raise TypeError("legacy SDK Circuit")
        return cls.from_qiskit(c.to_qiskit())
    @classmethod
    def from_qiskit(cls,qc):
        from qiskit import QuantumCircuit
        if type(qc) is not QuantumCircuit:raise TypeError("Qiskit QuantumCircuit")
        # Snapshot immediately, never retain or mutate the caller's circuit.
        # Packed conjugation semantics intentionally ignore global phase.
        if not 1<=qc.num_qubits<=64 or qc.num_clbits or qc.num_parameters or len(qc.data)>100_000:raise ValueError("circuit")
        qc=qc.copy()
        w={b:i for i,b in enumerate(qc.qubits)};buf=bytearray()
        for inst in qc.data:
            op=inst.operation;i=CODES.get(op.base_class)
            if i is None or inst.clbits or op.params or getattr(op,"condition",None) is not None:raise ValueError("gate")
            if len(inst.qubits)!=(2 if i==5 else 1) or (i==5 and op.ctrl_state!=1):raise ValueError("arity/control")
            a=w[inst.qubits[0]];b=w[inst.qubits[1]] if i==5 else 0
            buf.extend((i,a,b))
        return cls(qc.num_qubits,bytes(buf))
    def propagate(self,post,*,max_terms=4096,max_work=2_000_000):
        valid_pauli(post,self.width);bounds(max_terms,max_work)
        try:terms,k,peak,work=self.native.propagate(post,max_terms,max_work)
        except rn.BudgetExceeded as e:raise BudgetExceeded(str(e)) from e
        return Propagation(tuple(terms),k,peak,work)
    def verify(self,obs,*,max_terms=4096,max_work=2_000_000,adaptive=False):
        bounds(max_terms,max_work)
        if type(adaptive) is not bool or type(obs) is not tuple or not 1<=len(obs)<=64:raise ValueError("request")
        for ob in obs:
            if type(ob) is not Obligation:raise TypeError("obligation")
            valid_pauli(ob.pre,self.width);valid_pauli(ob.post,self.width)
        remaining=max_work;reports=[]
        for ob in obs:
            method="pyo3-exact"
            def report(status,reason,w=None):
                return Report(status,method,self.identity,digest(asdict(ob)),SCOPE,reason,w)
            if remaining<=0:reports.append(report("INCONCLUSIVE","term/work budget"));continue
            backend=self.native
            if adaptive:
                method="pyo3-cone"
                cost=3*(len(self.packed)//3)
                if cost>=remaining:reports.append(report("INCONCLUSIVE","preprocess budget"));remaining=0;continue
                remaining-=cost
                backend=rn.PackedCircuit(self.width,reduce_cone(self.packed,ob.post))
            try:ok,w,peak,work=backend.transition(ob.pre,ob.post,max_terms,remaining)
            except rn.BudgetExceeded:reports.append(report("INCONCLUSIVE","term/work budget"));remaining=0;continue
            remaining-=work
            wit=None if w is None else Witness(tuple(w[0]),tuple(w[1]),tuple(w[2]),w[3])
            reports.append(report("PASS" if ok else "FAIL","exact coefficient equality" if ok else "nonzero exact product-state expectation",wit))
        return tuple(reports)

def bounds(terms,work):
    if type(terms) is not int or not 1<=terms<=4096 or type(work) is not int or not 1<=work<=2_000_000:raise ValueError("budget")
@dataclass(frozen=True)
class TransitionContract:
    pre:tuple
    post:tuple
    def verify(self,circuit,*,adaptive=False):
        session=RustSession.from_circuit(circuit)
        return session.verify((Obligation(self.pre,self.post),),adaptive=adaptive)[0]
