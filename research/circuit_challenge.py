"""100 authored circuit challenge instances.

Only Ketary builds the candidate programs. NumPy/SciPy provide independent
analytic references, and Aer is required only for the measured cases.
Instances within a family vary inputs; these are not 100 distinct algorithms
or independent-user evidence.
"""
from collections import Counter
from dataclasses import dataclass
from itertools import product
from math import pi
import numpy as np
import ketary as q
from scipy.linalg import expm

@dataclass(frozen=True)
class Case:
    category: str
    name: str
    args: tuple

def group(category,name,args):
    return [Case(category,f"{name}-{i+1:02d}",tuple(a)) for i,a in enumerate(args)]

CASES=(
    group("fundamentals","single-rotation",[(axis,t) for axis in ("x","y","z") for t in (.31,-.82,1.7)])
    + group("fundamentals","phase-interference",[(.73,)])
    + group("entanglement","ghz",[(n,) for n in range(2,7)])
    + group("entanglement","graph",[(3,((0,1),(1,2))),(3,((0,2),(1,2))),(4,((0,1),(1,2),(2,3),(3,0))),(4,((0,1),(0,2),(0,3))),(5,((0,1),(2,3),(3,4)))])
    + group("algorithms","fourier",[(n,inv) for n in (2,3,4) for inv in (False,True)])
    + group("algorithms","bv",[(m,) for m in ("10","101","111","1001")])
    + group("algorithms","grover",[(m,) for m in ("00","10","111")])
    + group("algorithms","qpe",[(3,3),(4,11)])
    + group("parameters","bind",[(n,seed) for n in (2,3,4) for seed in (1101,2202,3303)])
    + group("parameters","sweep",[(n,seed) for n in (2,3) for seed in (1101,2202)])
    + group("parameters","sequential",[(2,1101),(3,2202)])
    + group("hamiltonians","pauli",[(label,t) for label in ("X","Y","Z","ZX","XYZ") for t in (.37,-.29)])
    + group("hamiltonians","commuting",[(t,) for t in (.2,-.4,.7)])
    + group("hamiltonians","identity",[(.37,)])
    + group("hamiltonians","noncommuting",[(.4,)])
    + group("oracles","parity",[(m,o) for m in ("1","10","101","111") for o in (0,1)])
    + group("oracles","constant",[(2,0),(3,1)])
    + group("syndrome","bit-syndrome",[(bits,error,False) for bits,error in ((0,None),(0,0),(1,1),(1,2),(1,None))])
    + group("syndrome","phase-syndrome",[(bits,error,True) for bits,error in ((0,None),(0,0),(1,1),(1,2),(1,None))])
    + group("dynamic","feedforward",[(0,),(1,)])
    + group("dynamic","reset",[(1,)])
    + group("dynamic","teleport",[(.27,.81),(-.8,.2)])
    + group("composition","remap",[(0,2),(2,0)])
    + group("composition","repeat",[(3,)])
    + group("composition","inverse",[(.41,)])
    + group("composition","copy-compose",[(.9,)])
    + group("verification","verdict",[(kind,) for kind in ("pass","fail","scope","contract","evidence")])
)
EXPECTED_COUNTS={"fundamentals":10,"entanglement":10,"algorithms":15,"parameters":15,"hamiltonians":15,"oracles":10,"syndrome":10,"dynamic":5,"composition":5,"verification":5}
assert len(CASES)==100 and len({c.name for c in CASES})==100
assert Counter(c.category for c in CASES)==EXPECTED_COUNTS

P={"I":np.eye(2,dtype=complex),"X":np.array([[0,1],[1,0]],complex),"Y":np.array([[0,-1j],[1j,0]],complex),"Z":np.diag([1.,-1.]).astype(complex)}
def pauli(label):
    a=np.array([[1]],complex)
    for p in label:a=np.kron(a,P[p])
    return a
def basis(n,i):return np.eye(1<<n,dtype=complex)[:,i]
def random_state(n,seed=1101):
    rng=np.random.default_rng(seed);v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);return v/np.linalg.norm(v)
def rot(axis,t):return np.cos(t/2)*P["I"]-1j*np.sin(t/2)*P[axis.upper()]
def on(n,i,m):
    out=np.array([[1]],complex)
    for wire in reversed(range(n)):out=np.kron(out,m if wire==i else P["I"])
    return out
def permutation(n,fn):
    out=np.zeros((1<<n,1<<n),complex)
    for i in range(1<<n):out[fn(i),i]=1
    return out
def cx(n,a,b):return permutation(n,lambda i:i^((1<<b) if i&(1<<a) else 0))
def close(got,want):
    np.testing.assert_allclose(got,want,rtol=0,atol=1e-9)
    return float(np.max(np.abs(np.asarray(got)-np.asarray(want))))
def strict(c,m):
    # Complete column test from every basis input, plus one complex input.
    # No Qiskit builder/operator is used to create expected output.
    n=c.num_qubits
    residual=max(close(c.run(initial_state=format(i,f"0{n}b")).math.statevector(),m[:,i]) for i in range(1<<n))
    v=random_state(n);return max(residual,close(c.run(initial_state=v).math.statevector(),m@v))
def template(n):
    p=q.Circuit.parameter_vector("t",n+1)
    c=q.Circuit.symbolic(n).ry(p[:n],range(n)).rzz(p[-1],pairs=q.chain(range(n)))
    return c,p
def parameter_matrix(n,row):
    a=np.array([[1]],complex)
    for t in reversed(row[:n]):a=np.kron(a,rot("y",t))
    diag=np.array([np.exp(-.5j*row[-1]*sum((-1)**(((i>>j)&1)^((i>>(j+1))&1)) for j in range(n-1))) for i in range(1<<n)])
    return diag[:,None]*a
def measured(c,expected):
    result=c.run_shots(shots=32,seed=1101)
    assert result.counts=={expected:32},result.counts
    return 0.
def run_case(case):
    name=case.name.rsplit("-",1)[0];a=case.args
    if name=="single-rotation":
        axis,t=a;c=getattr(q.Circuit(1),"r"+axis)(t,0)
        return strict(c,rot(axis,t))
    if name=="phase-interference":
        t,=a;c=q.Circuit(1).h(0).p(t,0).h(0)
        return close(c.run().math.statevector(),np.array([1+np.exp(1j*t),1-np.exp(1j*t)])/2)
    if name=="ghz":
        n,=a;c=q.ghz(n)
        return close(c.run().math.statevector(),(basis(n,0)+basis(n,(1<<n)-1))/np.sqrt(2))
    if name=="graph":
        n,edges=a;c=q.Circuit(n).h(range(n)).cz(pairs=edges)
        want=np.array([(-1)**sum(((i>>u)&1)*((i>>v)&1) for u,v in edges) for i in range(1<<n)])/np.sqrt(1<<n)
        return close(c.run().math.statevector(),want)
    if name=="fourier":
        n,inv=a;N=1<<n
        want=np.exp(((-1 if inv else 1)*2j*pi/N)*np.outer(np.arange(N),np.arange(N)))/np.sqrt(N)
        return strict(q.qft(n,inverse=inv),want)
    if name=="bv":
        mask,=a;n=len(mask);r=q.bernstein_vazirani(mask).run()
        k=int(mask,2);return close(r.math.statevector(),(basis(n+1,k)-basis(n+1,k+(1<<n)))/np.sqrt(2))
    if name=="grover":
        marked,=a;n=len(marked);N=1<<n
        iterations=int(pi/(4*np.arcsin(1/np.sqrt(N))))
        angle=(2*iterations+1)*np.arcsin(1/np.sqrt(N))
        want=np.full(N,np.cos(angle)/np.sqrt(N-1),complex);want[int(marked,2)]=np.sin(angle)
        return close(q.grover(marked).run().math.statevector(),want)
    if name=="qpe":
        n,k=a
        return close(q.phase_estimation(k/(1<<n),precision=n).run().math.statevector(),basis(n+1,k+(1<<n)))
    if name in ("bind","sweep","sequential"):
        n,seed=a;rng=np.random.default_rng(seed);rows=rng.uniform(-1,1,(3,n+1));c,p=template(n)
        before=c.parameters
        if name=="bind":
            errors=[strict(c.bind(dict(zip(p,row,strict=True))),parameter_matrix(n,row)) for row in rows]
        elif name=="sweep":
            errors=[close(r.math.statevector(),parameter_matrix(n,row)[:,0]) for r,row in zip(c.sweep_rows(rows).run(),rows,strict=True)]
        else:
            out=q.Circuit(n);want=np.eye(1<<n, dtype=complex)
            for row in rows:
                out.apply(c.bind(row));want=parameter_matrix(n,row)@want
            errors=[strict(out,want)]
        assert c.parameters==before
        return max(errors)
    if name=="pauli":
        label,t=a;n=len(label)
        return strict(q.Circuit(n).evolve(q.Observable({label:1.}),time=t),expm(-1j*t*pauli(label)))
    if name=="commuting":
        t,=a;H={"XX":.7,"YY":-.31,"ZZ":.21,"II":.9}
        return strict(q.Circuit(2).evolve(q.Observable(H),time=t),expm(-1j*t*sum(v*pauli(k) for k,v in H.items())))
    if name=="identity":
        t,=a
        return strict(q.Circuit(3).evolve(q.I(),time=t),np.exp(-1j*t)*np.eye(8))
    if name=="noncommuting":
        t,=a;c=q.Circuit(1).h(0)
        try:c.evolve(q.X(0)+q.Z(0),time=t)
        except q.UnsupportedOperation:return close(c.run().math.statevector(),np.ones(2)/np.sqrt(2))
        raise AssertionError("noncommuting evolution accepted")
    if name=="parity":
        mask,offset=a;n=len(mask);m=int(mask,2)
        want=permutation(n+1,lambda i:i^((((i&m).bit_count()%2)^offset)<<n))
        return strict(q.parity_oracle(mask,offset=offset),want)
    if name=="constant":
        n,value=a
        return strict(q.constant_oracle(n,value=value),permutation(n+1,lambda i:i^(value<<n)))
    if name in ("bit-syndrome","phase-syndrome"):
        bit,error,phase=a;c=q.Circuit.classical(5,2)
        if bit:c.x([0,1,2])
        if phase:c.h([0,1,2])
        if error is not None:(c.z if phase else c.x)(error)
        if phase:c.h([0,1,2])
        c.cx(pairs=[(0,3),(1,3),(1,4),(2,4)]).measure([3,4],[0,1])
        return measured(c,{None:"00",0:"01",1:"11",2:"10"}[error])
    if name=="feedforward":
        bit,=a;c=q.Circuit.classical(2,2)
        if bit:c.x(0)
        c.measure(0,0).if_x(1,0).measure(1,1)
        return measured(c,"11" if bit else "00")
    if name=="reset":
        c=q.Circuit.classical(1,1).x(0).reset(0).measure(0,0)
        return measured(c,"0")
    if name=="teleport":
        t,p=a;result=q.teleportation(t,p,verify=True).run_shots(shots=64,seed=1101)
        assert sum(result.counts.values())==64 and all(k[0]=="0" for k,v in result.counts.items() if v)
        return 0.
    if name=="remap":
        x,y=a;block=q.Circuit(2).h(0).cx(0,1)
        return strict(q.Circuit(3).apply(block,wires=[x,y]),cx(3,x,y)@on(3,x,np.array([[1,1],[1,-1]])/np.sqrt(2)))
    if name=="repeat":
        k,=a;c=q.Circuit(2).ry(.27,0).cx(0,1)
        m=cx(2,0,1)@on(2,0,rot("y",.27))
        return strict(c.repeat(k),np.linalg.matrix_power(m,k))
    if name=="inverse":
        t,=a;c=q.Circuit(2).ry(t,0).cx(0,1)
        return strict(c.copy().apply(c.inverse()),np.eye(4))
    if name=="copy-compose":
        t,=a;c=q.Circuit(2).ry(t,0);out=c.compose(q.Circuit(2).cx(0,1))
        return max(strict(c,on(2,0,rot("y",t))),strict(out,cx(2,0,1)@on(2,0,rot("y",t))))
    if name=="verdict":
        kind,=a;c=q.bell();r=c.run()
        if kind=="pass":assert r.test.expectation("ZZ",1).status=="PASS"
        elif kind=="fail":assert r.test.expectation("ZZ",-1).status=="FAIL"
        elif kind=="contract":
            contract=c.contract(expectations={"ZZ":1,"XX":1})
            assert contract.verify(r).status=="PASS" and contract.verify(c.copy().z(0).run()).status=="FAIL"
        elif kind=="scope":
            assert q.Circuit(2).z(0).test.compare(q.Circuit(2),inputs=["00"],complete=False).status=="INCONCLUSIVE"
        else:
            report=q.Circuit(2).x(0).test.compare(q.Circuit(2),inputs=["00"],complete=False)
            assert report.status=="FAIL" and report.evidence.reproduce()["reproduced"]
        return 0.
    raise AssertionError(f"unhandled case {case}")

def manifest():
    return [{"id":c.name,"category":c.category,"args":c.args,"oracle":"measured ideal counts" if c.category in ("dynamic","syndrome") else "explicit analytic or verdict contract"} for c in CASES]
