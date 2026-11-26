"""Disjoint authored qualification seeds; independent closed-form gate matrices."""
import numpy as np
import pytest
import ketary as q
from qiskit.quant_info import Operator
from ketary._gate_specs import SPECS

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.diag([1,-1]).astype(complex)
H=(X+Z)/np.sqrt(2)
S=np.diag([1,1j])
T=np.diag([1,np.exp(1j*np.pi/4)])
SX=((1+1j)*I+(1-1j)*X)/2
SWAP=np.eye(4,dtype=complex)[:,[0,2,1,3]]
SINGLE={"h":H,"x":X,"y":Y,"z":Z,"s":S,"sdg":S.conj().T,
        "t":T,"tdg":T.conj().T,"sx":SX,"sxdg":SX.conj().T}
PAULI={"x":X,"y":Y,"z":Z}
NAMES=tuple(SINGLE)+("rx","ry","rz","p","u","cx","cy","cz","ch","cp",
                     "crx","cry","crz","swap","ccx","cswap","rxx","ryy","rzz")
SEEDS=(83119,83131,83171)

def rotation(a,t):
    return np.cos(t/2)*np.eye(len(a))-1j*np.sin(t/2)*a

def controlled(a,k=1):
    # Local wire 0 is the low-order control; target block occupies high bits.
    d=1<<k;out=np.eye(d*len(a),dtype=complex)
    indices=np.arange(len(a))*d+d-1
    out[np.ix_(indices,indices)]=a
    return out

def local(name,angles):
    t=angles[0]
    if name in SINGLE:return SINGLE[name],0
    if name in ("rx","ry","rz"):return rotation(PAULI[name[-1]],t),1
    if name=="p":return np.diag([1,np.exp(1j*t)]),1
    if name=="u":
        a,b,c=angles
        return np.array([[np.cos(a/2),-np.exp(1j*c)*np.sin(a/2)],
                         [np.exp(1j*b)*np.sin(a/2),np.exp(1j*(b+c))*np.cos(a/2)]]),3
    if name=="swap":return SWAP,0
    if name=="ccx":return controlled(X,2),0
    if name=="cswap":return controlled(SWAP),0
    if name in ("cx","cy","cz","ch"):return controlled(SINGLE[name[-1]]),0
    if name=="cp":return controlled(np.diag([1,np.exp(1j*t)])),1
    if name.startswith("cr"):return controlled(rotation(PAULI[name[-1]],t)),1
    if name in ("rxx","ryy","rzz"):return rotation(np.kron(PAULI[name[-1]],PAULI[name[-1]]),t),1
    raise AssertionError(name)

def embed(matrix,n,wires):
    out=np.zeros((1<<n,1<<n),complex)
    for column in range(1<<n):
        local_column=sum(((column>>w)&1)<<i for i,w in enumerate(wires))
        outside=column
        for w in wires:outside&=~(1<<w)
        for row in range(len(matrix)):
            target=outside|sum(((row>>i)&1)<<w for i,w in enumerate(wires))
            out[target,column]=matrix[row,local_column]
    return out

def test_catalog():
    assert set(NAMES)==set(SPECS)

@pytest.mark.parametrize("seed",SEEDS)
@pytest.mark.parametrize("name",NAMES)
def test_independent_gate_matrix(seed,name):
    rng=np.random.default_rng(seed);angles=rng.uniform(-4,4,3)
    matrix,count=local(name,angles)
    n=4;wires=rng.choice(n,int(np.log2(len(matrix))),replace=False).tolist()
    c=q.Circuit(n).evolve(q.I(),time=.271)
    getattr(c,name)(*angles[:count].tolist(),*wires)
    want=np.exp(-.271j)*embed(matrix,n,wires)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,want,atol=1e-9,rtol=0)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),want@v,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(c.inverse().to_qiskit()).data,want.conj().T,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(q.Circuit.from_json(c.to_json()).to_qiskit()).data,want,atol=1e-9,rtol=0)

@pytest.mark.parametrize("controls",range(3,8))
def test_independent_mcx(controls):
    n=controls+1;wires=list(reversed(range(n)))
    c=q.Circuit(n).mcx(wires[:-1],wires[-1])
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,embed(controlled(X,controls),n,wires),atol=1e-9,rtol=0)

@pytest.mark.parametrize("path,cap",[
    ("run",64),("run_many",320),("statevector",64),("density",256),
    ("grouped",8),("selected",256),("checkpoint",128)])
def test_exact_resource_boundary(path,cap,monkeypatch):
    c=q.bell();r=c.run()
    contract=q.Contract(2,expectations={"XX":1})
    c.checkpoint("bell")
    routes={
        "run":lambda b:c.run(max_bytes=b),
        "run_many":lambda b:c.run_many(["00","11"],max_bytes=b),
        "statevector":lambda b:r.math.statevector(max_bytes=b),
        "density":lambda b:r.math.density_matrix(max_bytes=b),
        "grouped":lambda b:r.math.expectations(["XX","ZZ"],max_work=b),
        "selected":lambda b:c.test.compare(c,inputs=["00"],complete=False,max_bytes=b),
        "checkpoint":lambda b:c.debug.verify_checkpoints({"bell":contract},max_bytes=b)}
    fn=routes[path]
    with pytest.raises(q.ResourceLimit):fn(cap-1)
    fn(cap);fn(cap+1)
    if path in ("run","run_many","selected","checkpoint"):
        from ketary import _execution,_trace
        def fail(*a,**k):pytest.fail("native evolution before resource admission")
        monkeypatch.setattr(_execution,"execute_ideal",fail)
        monkeypatch.setattr(_trace,"_Cursor",fail)
        with pytest.raises(q.ResourceLimit):fn(cap-1)

def test_grouped_late_invalid_before_native(monkeypatch):
    r=q.bell().run()
    def fail(*a,**k):pytest.fail("native Pauli evaluation before complete preflight")
    monkeypatch.setattr(type(r.math),"_native_pauli_values",fail)
    with pytest.raises(ValueError):r.math.expectations(["XX","invalid"])
