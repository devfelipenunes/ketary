"""Independent mathematical oracles and backend failure-path checks."""
import sys
import types
import numpy as np
import pytest
import ketary as q

@pytest.mark.parametrize("seed",[1101,2202,3303])
@pytest.mark.parametrize("wires",[(2,0),(0,2),(1,)])
def test_reduced_state_against_explicit_bit_index_oracle(seed,wires):
    n=3;rng=np.random.default_rng(seed)
    v=rng.normal(size=8)+1j*rng.normal(size=8);v/=np.linalg.norm(v)
    result=q.Result(v)
    rest=tuple(w for w in range(n) if w not in wires)
    def index(i,selected):
        out=0
        for w in selected:out=2*out+((i>>w)&1)
        return out
    d=1<<len(wires);rho=np.zeros((d,d),complex)
    for i in range(8):
        for j in range(8):
            if index(i,rest)==index(j,rest):
                rho[index(i,wires),index(j,wires)]+=v[i]*v[j].conjugate()
    np.testing.assert_allclose(result.math.density_matrix(wires),rho,atol=1e-12,rtol=0)
    p=result.math.marginal_probabilities(wires)
    np.testing.assert_allclose(list(p.values()),rho.diagonal().real,atol=1e-12,rtol=0)
    assert result.math.purity(wires)==pytest.approx(np.trace(rho@rho).real,abs=1e-12)
    vals=np.linalg.eigvalsh(rho)
    vals=vals[vals>1e-13]
    entropy=-sum(vals*np.log2(vals))
    assert result.math.entropy((wires,rest))==pytest.approx(entropy,abs=1e-12)
    s=result.math.schmidt(wires)
    np.testing.assert_allclose(np.sort(s*s)[-len(vals):],vals,atol=1e-12,rtol=0)
    def mass(assign):
        return sum(abs(v[i])**2 for i in range(8) if all((i>>w)&1==b for w,b in assign.items()))
    assert result.math.conditional_probability({2:1},{0:0})==pytest.approx(mass({2:1,0:0})/mass({0:0}),abs=1e-12)

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_observable_variance_independent_dense_oracle(seed):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=8)+1j*rng.normal(size=8);v/=np.linalg.norm(v)
    matrices={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),
              "Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    terms={"XYZ":.7,"YIX":-.3,"IIZ":1.2,"III":.17}
    h=sum(coef*np.kron(np.kron(matrices[label[0]],matrices[label[1]]),matrices[label[2]]) for label,coef in terms.items())
    mean=np.vdot(v,h@v).real
    variance=np.linalg.norm(h@v-mean*v)**2
    result=q.Result(v);observable=q.Observable(terms)
    assert result.math.expectation(observable)==pytest.approx(mean,abs=1e-12)
    assert result.math.observable_variance(observable)==pytest.approx(variance,abs=1e-12)
    assert result.math.observable_variance_streamed(observable)==pytest.approx(variance,abs=1e-12)
    assert result.math.variance(observable)==pytest.approx(variance,abs=1e-12)

def test_observable_native_duplicate_and_imaginary_aggregation():
    from qiskit.quantum_info import SparsePauliOp
    op=SparsePauliOp.from_list([("Z",1+2j),("Z",2-2j),("X",0)])
    assert q.Observable.from_qiskit(op).to_dict()=={"Z":3.}
    with pytest.raises(ValueError):q.Observable.from_qiskit(SparsePauliOp.from_list([("Z",1+1j)]))
    with pytest.raises(ValueError):q.Observable.from_qiskit(SparsePauliOp.from_list([("Z",float("inf"))]))

@pytest.mark.parametrize("kwargs",[{},{"subsystems":[()]},{"subsystems":[(0,0)]},{"subsystems":[(0,),(0,)]},{"bits":["0"]}])
def test_invalid_query_plan(kwargs):
    with pytest.raises(ValueError):q.bell().plan(**kwargs)

def test_query_plan_snapshot_single_run_and_preflight(monkeypatch):
    c=q.bell();plan=c.plan(bits=["00","11"],paulis=["XX"],subsystems=[(0,)])
    c.x(0)
    original=q.Circuit.run;calls=[]
    def run(self,*a,**k):
        calls.append(1);return original(self,*a,**k)
    monkeypatch.setattr(q.Circuit,"run",run)
    with pytest.raises(q.ResourceLimit):plan.run(max_bytes=127)
    assert not calls
    report=plan.run()
    assert len(calls)==1
    assert report["evidence"]["basis"]["00"]["probability"]==pytest.approx(.5)
    assert report["evidence"]["expectations"]["XX"]==pytest.approx(1.)
    np.testing.assert_allclose(report["density_matrices"][0]["real"],np.eye(2)/2,atol=1e-12,rtol=0)

def test_checkpoint_names_and_first_nonpass():
    c=q.Circuit(2).checkpoint("initial").h(0).checkpoint("superposition").cx(0,1).checkpoint("bell")
    contract=c.contract(expectations={"ZZ":1})
    with pytest.raises(ValueError):c.debug.verify_checkpoints({0:contract,"initial":contract})
    with pytest.raises(q.ResourceLimit):c.debug.verify_checkpoints({"bell":contract},max_steps=1)
    with pytest.raises(ValueError):c.debug.verify_checkpoints({"missing":contract})
    report=c.debug.verify_checkpoints({"initial":contract,"superposition":contract,"bell":contract})
    assert report.status=="FAIL" and report["first_nonpass"]==1
    assert len(report["checks"])==2
    assert c.debug.compare(q.Circuit(3)).check.status=="UNSUPPORTED"
    assert c.debug.compare(c.copy(),max_bytes=1).check.status=="UNSUPPORTED"

@pytest.mark.parametrize("success,counts",[(False,{}),(True,{"0":7}),(True,{"2":8}),(True,{"0":8.0}),(True,{"0":9,"1":-1}),(True,None),(True,[]),(True,[{"0":8}]),(True,{0:8}),(True,{"0":"8"}),(True,{"0":None}),(True,{"0":True,"1":7})])
def test_dynamic_backend_invalid_result_is_rejected(monkeypatch,success,counts):
    import qiskit
    class FakeBackend:
        def __init__(self,**kwargs):pass
        def run(self,*a,**k):return self
        def result(self):return types.SimpleNamespace(success=success,get_counts=lambda:counts)
    fake=types.ModuleType("qiskit_aer");fake.AerSimulator=FakeBackend
    monkeypatch.setitem(sys.modules,"qiskit_aer",fake)
    monkeypatch.setattr(qiskit,"transpile",lambda circuit,**kwargs:circuit)
    c=q.Circuit.classical(1,1).measure(0,0)
    with pytest.raises(RuntimeError):c.run_shots(shots=8,seed=1)

def test_dynamic_seed_preflight_before_backend():
    c=q.Circuit.classical(1,1).measure(0,0)
    with pytest.raises(ValueError):c.run_shots(seed=2**32)

def test_operator_scope_and_width():
    c=q.bell()
    assert c.test.equivalent(q.Circuit(3)).status=="FAIL"
    assert c.test.metrics(q.Circuit(3)).status=="FAIL"
    assert c.test.equivalent(c.copy(),max_bytes=1).status=="UNSUPPORTED"
    assert c.test.metrics(c.copy(),max_bytes=1).status=="UNSUPPORTED"
