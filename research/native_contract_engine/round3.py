"""Round 3: real Ketary export, batch, sparse Clifford+T, leakage witnesses.
Research-only paths, not public APIs. No timing thresholds.
"""
import ctypes as C
import json, random, statistics, time, subprocess, platform
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit.library import HGate,SGate,SdgGate,XGate,ZGate,CXGate,TGate,TdgGate
from qiskit.quantum_info import Operator, Pauli, Clifford
from benchmark import ROOT, OPS, build, label, pack, py, export, load, invoke, random_g
from sparse import propagate, invariant, BudgetExceeded
from dataclasses import dataclass

RNG=random.Random(20261127)
CLASSES=(HGate,SGate,SdgGate,XGate,ZGate,CXGate,TGate,TdgGate)
CODES={k:i for i,k in enumerate(CLASSES)}

@dataclass(frozen=True)
class Prepared:
    width: int
    gates: tuple
    packed: bytes

def prepare(c,*,allow_t=False):
    native=c.to_qiskit()
    if native.num_clbits or native.num_parameters or not 1<=native.num_qubits<=64 or len(native.data)>100_000:
        raise ValueError("unsupported circuit")
    wires={w:i for i,w in enumerate(native.qubits)}
    rows=[];buf=bytearray()
    for inst in native.data:
        op=inst.operation
        i=CODES.get(op.base_class)
        if i is None or (i>=6 and not allow_t) or inst.clbits or op.params or getattr(op,"condition",None) is not None:
            raise ValueError("unsupported gate")
        if len(inst.qubits)!=(2 if i==5 else 1):raise ValueError("arity")
        a=wires[inst.qubits[0]];b=wires[inst.qubits[1]] if i==5 else 0
        if i==5 and a==b:raise ValueError("duplicate wires")
        rows.append((i,a,b));buf.extend((i,a,b))
    return Prepared(native.num_qubits,tuple(rows),bytes(buf))

def timed(routes):
    raw={k:[] for k in routes}
    for f in routes.values():
        for _ in range(3):f()
    for _ in range(11):
        keys=list(routes);RNG.shuffle(keys)
        for k in keys:
            t=time.perf_counter_ns();routes[k]();raw[k].append((time.perf_counter_ns()-t)/1e6)
    return {k:{"median_ms":statistics.median(v),"p95_ms":float(np.percentile(v,95)),"samples_ms":v} for k,v in raw.items()}

def batch():
    subprocess.run(["g++","-std=c++17","-O3","-shared","-fPIC",str(ROOT/"batch.cpp"),"-o",str(ROOT/"batch.so")],check=True)
    # scalar shared library produced by first benchmark.
    scalar=load("cpp.so")
    dll=C.CDLL(str(ROOT/"batch.so"));fn=dll.batch_bitslice
    fn.argtypes=[C.POINTER(C.c_uint8),C.c_size_t,C.c_uint32,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64),C.POINTER(C.c_uint8),C.c_size_t];fn.restype=C.c_int
    def call(pre,ps):
        b=(C.c_uint8*len(pre.packed)).from_buffer_copy(pre.packed)
        m=len(ps);x=(C.c_uint64*m)(*(p[0] for p in ps));z=(C.c_uint64*m)(*(p[1] for p in ps));r=(C.c_uint8*m)(*(p[2] for p in ps))
        if fn(b,len(b)//3,pre.width,x,z,r,m):raise ValueError("native rejection")
        return list(zip(x,z,r))
    checks=0
    for n in (2,3,4,5):
        for _ in range(8):
            c=q.from_qiskit(build(n,random_g(n,25)));pre=prepare(c)
            ps=[(RNG.getrandbits(n),RNG.getrandbits(n),RNG.randrange(2)) for _ in range(64)]
            qc=c.to_qiskit();u=Operator(qc).data
            for p,v in zip(ps,call(pre,ps)):
                expected=Pauli(label(n,p));got=Pauli(label(n,v))
                np.testing.assert_allclose(got.to_matrix(),u.conj().T@expected.to_matrix()@u,atol=1e-10)
                assert got==expected.evolve(qc,frame="h");checks+=1
    c=q.from_qiskit(build(2,[(0,0,0)]));pre=prepare(c);c.z(0)
    assert pre.gates==((0,0,0),) and prepare(c).gates!=pre.gates
    for gate in ("t","reset"):
        c=QuantumCircuit(2);getattr(c,gate)(0)
        try:prepare(q.from_qiskit(c))
        except (ValueError,TypeError):pass
        else:raise AssertionError("unsupported gate admitted")
    rows=[]
    for n in (16,32):
        for count in (100,1000,10000):
            g=random_g(n,count);c=q.from_qiskit(build(n,g));pre=prepare(c);qc=c.to_qiskit();cl=Clifford(qc)
            assert pre.gates==tuple(g) and pre.packed==bytes(export(c))
            for m in (1,8,32,64):
                ps=[(RNG.getrandbits(n),RNG.getrandbits(n),RNG.randrange(2)) for _ in range(m)]
                paulis=[Pauli(label(n,p)) for p in ps];buf=pack(g)
                got=call(pre,ps);assert got==[invoke(scalar,buf,n,p) for p in ps]
                assert [Pauli(label(n,v)) for v in got]==[p.evolve(cl,frame="h") for p in paulis]
                routes={"native_scalar_prepared":lambda:[invoke(scalar,buf,n,p) for p in ps],
                        "native_batch_prepared":lambda:call(pre,ps),
                        "native_batch_export":lambda:call(prepare(c),ps),
                        "legacy_export_only":lambda:export(c),
                        "prepare_only":lambda:prepare(c),
                        "qiskit_clifford_prepared":lambda:[p.evolve(cl,frame="h") for p in paulis],
                        "qiskit_clifford_export":lambda:qiskit_batch(c,paulis)}
                rows.append({"n":n,"gates":count,"m":m,"timings":timed(routes)})
    return {"dense_checks":checks,"rows":rows}

def qiskit_batch(c,ps):
    cl=Clifford(c.to_qiskit())
    return [p.evolve(cl,frame="h") for p in ps]

def sparse_study():
    checks=0;err=0.
    for n in (1,2,3,4,5):
        for _ in range(40):
            gs=[];c=QuantumCircuit(n)
            for j in range(30):
                op=RNG.randrange(8);a=RNG.randrange(n)
                if op==5 and n==1:op=0
                b=RNG.choice([i for i in range(n) if i!=a]) if op==5 else 0
                gs.append((op,a,b))
                if op==5:c.cx(a,b)
                else:getattr(c,(OPS+("t","tdg"))[op])(a)
            kc=q.from_qiskit(c);pre=prepare(kc,allow_t=True);assert pre.gates==tuple(gs)
            p=(RNG.getrandbits(n),RNG.getrandbits(n),RNG.randrange(2));r=propagate(n,pre.gates,p)
            u=Operator(c).data;actual=sum(((a+b*np.sqrt(2))/(2**r.denominator_power)*Pauli(label(n,(x,z,0))).to_matrix() for x,z,a,b in r.terms),np.zeros_like(u))
            e=float(np.max(np.abs(actual-u.conj().T@Pauli(label(n,p)).to_matrix()@u)));assert e<1e-10;err=max(err,e);checks+=1
    rows=[]
    for n in (16,32,64):
        for t in (0,4,8,12,13):
            for kind in ("commuting","branching"):
                c=QuantumCircuit(n)
                for i in range(t):c.t(i)
                kc=q.from_qiskit(c);pre=prepare(kc,allow_t=True)
                p=(0,(1<<n)-1,0) if kind=="commuting" else ((1<<n)-1,0,0)
                def run(pr):
                    try:return propagate(n,pr.gates,p)
                    except BudgetExceeded:return None
                r=run(pre);assert (r is None)==(kind=="branching" and t==13)
                if r is not None:
                    assert len(r.terms)==(1 if kind=="commuting" else 2**t)
                    assert invariant(r,p)==(kind=="commuting" or t==0)
                rows.append({"n":n,"T":t,"kind":kind,"status":"INCONCLUSIVE" if r is None else ("PASS" if invariant(r,p) else "FAIL"),"terms":None if r is None else len(r.terms),"timings":timed({"prepared":lambda:run(pre),"export_and_propagate":lambda:run(prepare(kc,allow_t=True))})})
    return {"dense_checks":checks,"max_error":err,"rows":rows}

def leakage(u,wire,tol=1e-9):
    # Own numeric input; admission is not a certified error bound.
    n=(len(u)).bit_length()-1
    if u.shape!=(1<<n,1<<n) or not 1<=n<=6 or not 0<=wire<n or not np.isfinite(u).all():raise ValueError("admission")
    if np.linalg.norm(u.conj().T@u-np.eye(len(u)),ord=2)>1e-12:raise ValueError("not unitary")
    clean=np.array([i for i in range(len(u)) if not i&(1<<wire)])
    dirty=clean|(1<<wire);a=u[np.ix_(dirty,clean)]
    _,s,vh=np.linalg.svd(a,full_matrices=False);v=vh[0].conj();p=float(s[0]**2)
    witness=np.zeros(len(u),complex);witness[clean]=v
    gap=float(np.linalg.norm((u@witness)[dirty])**2)
    if abs(gap-p)>1e-10:raise ArithmeticError("witness mismatch")
    status="PASS" if p<tol-1e-12 else ("FAIL" if p>tol+1e-12 and gap>tol+1e-12 else "INCONCLUSIVE")
    return status,p,witness,gap

def ancilla():
    rows=[]
    for n in (3,5,6):
        for wire in (0,n-1):
            for kind in ("clean","boundary","dirty"):
                c=QuantumCircuit(n);data=1 if wire==0 else 0;c.h(data);c.cx(data,wire);c.z(wire);c.cx(data,wire)
                theta={"clean":0.,"boundary":2*np.arcsin(np.sqrt(1e-9)),"dirty":.3}[kind]
                c.ry(theta,wire);kc=q.from_qiskit(c);u=Operator(kc.to_qiskit()).data
                s,p,w,gap=leakage(u,wire)
                assert s=={"clean":"PASS","boundary":"INCONCLUSIVE","dirty":"FAIL"}[kind]
                assert abs(p-np.sin(theta/2)**2)<1e-10
                P=np.diag([not i&(1<<wire) for i in range(len(u))]).astype(complex)
                def effect():
                    a=P-u.conj().T@P@u
                    return np.linalg.eigh((a+a.conj().T)/2)
                vals,vecs=effect();assert abs(float(vals[-1])**2-p)<1e-10
                assert abs(np.vdot(vecs[:,-1],(P-u.conj().T@P@u)@vecs[:,-1]).real-vals[-1])<1e-10
                rows.append({"n":n,"wire":wire,"kind":kind,"status":s,"leak":p,"witness_gap":gap,"timings":timed({"leakage_admitted":lambda:leakage(u,wire),"effect_kernel":effect,"export_operator_leakage":lambda:leakage(Operator(kc.to_qiskit()).data,wire)})})
    try:leakage(np.eye(4)*.9,0)
    except ValueError:pass
    else:raise AssertionError("nonunitary admitted")
    return {"checks":len(rows),"rows":rows}

if __name__=="__main__":
    print(json.dumps({"scope":"research only; batch exact Pauli transformation, sparse exact ring (no truncation), numeric leakage with separate probabilistic tolerance and diagnostic gray band; no public report, no RSS", "python":platform.python_version(),"batch":batch(),"sparse":sparse_study(),"ancilla":ancilla()},indent=2,allow_nan=False))
