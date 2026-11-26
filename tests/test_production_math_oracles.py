"""Production candidate mathematical properties with independent NumPy oracles.

Fixed seeds, small dense systems, no native Qiskit reference matrices.
The reference implementation is intentionally test-only.
"""
import itertools
import numpy as np
import pytest
import ketary as q

ATOL=1e-9
PAULI={
    "I":np.eye(2,dtype=complex),
    "X":np.array([[0,1],[1,0]],complex),
    "Y":np.array([[0,-1j],[1j,0]],complex),
    "Z":np.diag([1.,-1.]).astype(complex),
}

def dense(label):
    out=np.array([[1.]],complex)
    for p in label:
        out=np.kron(out,PAULI[p])
    return out

def state(n,seed):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    return v/np.linalg.norm(v)

def terms(n,seed):
    rng=np.random.default_rng(seed)
    labels=["".join(p) for p in itertools.product("IXYZ",repeat=n)]
    chosen=rng.choice(labels,size=min(8,len(labels)),replace=False)
    return {str(p):float(rng.uniform(-1,1)) for p in chosen}

def close(a,b,atol=ATOL):
    np.testing.assert_allclose(a,b,rtol=0,atol=atol)

def partial(v,n,wires):
    """Index-based reference, independent of runtime reshape/transpose."""
    size=1<<len(wires)
    rest=tuple(w for w in range(n) if w not in wires)
    def index(a,e):
        return sum(((a>>(len(wires)-1-i))&1)<<w for i,w in enumerate(wires))+sum(((e>>i)&1)<<w for i,w in enumerate(rest))
    out=np.zeros((size,size),complex)
    for a in range(size):
        for b in range(size):
            out[a,b]=sum(v[index(a,e)]*v[index(b,e)].conjugate() for e in range(1<<len(rest)))
    return out

@pytest.mark.parametrize("n",[1,2,3,4,5])
@pytest.mark.parametrize("seed",range(12))
def test_born_and_pauli_expectation_variance(n,seed):
    v=state(n,1101+seed);r=q.Result(v)
    coeff=terms(n,2202+seed);H=q.Observable(coeff)
    M=sum(w*dense(p) for p,w in coeff.items());mu=np.vdot(v,M@v)
    var=np.linalg.norm((M-mu*np.eye(len(v)))@v)**2
    close(mu.imag,0)
    close(r.math.expectation(H),mu.real)
    close(r.math.variance(H),var)
    close(r.math.observable_variance(H),var)
    # The smallest admitted four-state payload exercises fallback/short chunks.
    close(r.math.observable_variance_streamed(H,max_bytes=64*len(v)),var)
    probabilities=r.math.probabilities()
    close([probabilities[format(i,f"0{n}b")] for i in range(len(v))],abs(v)**2)
    close(sum(probabilities.values()),1)
    close(r.math.expectation(H+2),mu.real+2)
    close(r.math.variance(H+2),var)
    close(r.math.variance(-2*H),4*var)
    phase=q.Result(v*np.exp(1j*.73))
    close(phase.math.expectation(H),mu.real)
    close(phase.math.variance(H),var)
    close(r.math.fidelity(phase),1)
    copy=r.math.statevector();copy[:]=0
    close(r.math.statevector(),v)

@pytest.mark.parametrize("n",[2,3,4,5])
@pytest.mark.parametrize("seed",range(12))
def test_reduced_density_schmidt_entropy(n,seed):
    v=state(n,3303+seed);r=q.Result(v)
    rng=np.random.default_rng(seed)
    wires=tuple(int(w) for w in rng.permutation(n)[:1+seed%(n-1)])
    rho=partial(v,n,wires)
    actual=r.math.density_matrix(wires)
    close(actual,rho);close(actual,actual.conj().T);close(np.trace(actual),1)
    eig=np.linalg.eigvalsh(rho)
    assert eig.min()>=-ATOL
    close(r.math.purity(wires),np.trace(rho@rho).real)
    positive=eig[eig>1e-12]
    rest=tuple(w for w in range(n) if w not in wires)
    close(r.math.entropy((wires,rest)),-np.sum(positive*np.log2(positive)))
    sv=np.asarray(r.math.schmidt(wires))
    close(np.sort(sv**2),np.sort(eig)[-len(sv):])
    probs=r.math.marginal_probabilities(wires)
    close([probs.get(format(i,f"0{len(wires)}b"),0.) for i in range(len(rho))],rho.diagonal().real)
    close(r.math.density_matrix(tuple(reversed(wires))),partial(v,n,tuple(reversed(wires))))

@pytest.mark.parametrize("n",[2,3,4])
@pytest.mark.parametrize("seed",range(12))
def test_exact_commuting_evolution_strict_phase(n,seed):
    rng=np.random.default_rng(seed+4404);t=float(rng.uniform(-1,1))
    # Z strings commute, include nonzero identity and asymmetry in wire order.
    coeff={"I"*n:.31,"Z"+"I"*(n-1):.7,"I"*(n-1)+"Z":-.23,"Z"*n:.41}
    H=q.Observable(coeff);M=sum(w*dense(p) for p,w in coeff.items())
    val,V=np.linalg.eigh(M);U=(V*np.exp(-1j*t*val))@V.conj().T
    c=q.Circuit(n).evolve(H,time=t)
    # Compare every computational-basis column, including strict phase.
    for i in range(1<<n):
        v=np.eye(1<<n,dtype=complex)[:,i]
        close(c.run(initial_state=v).math.statevector(),U@v)
    v=state(n,seed);p=q.Circuit.parameter("t")
    symbolic=q.Circuit.symbolic(n).evolve(H,time=p)
    close(symbolic.bind({p:t}).run(initial_state=v).math.statevector(),U@v)
    close(c.inverse().run(initial_state=U@v).math.statevector(),v)

@pytest.mark.parametrize("seed",range(24))
def test_shared_jacobian_against_closed_form(seed):
    a,b=q.Circuit.parameter_vector("p",2)
    rng=np.random.default_rng(seed+5505);x,y=map(float,rng.uniform(-.9,.9,2))
    # Same axis lets the full derivative be derived without numerical shifts.
    c=q.Circuit.symbolic(1).ry(a,0).ry(a*b,0).ry(2*b,0).evolve(q.I(),time=a-b)
    angle=x+x*y+2*y
    expected=np.array([[-np.sin(angle)*(1+y),-np.sin(angle)*(x+2)],
                        [np.cos(angle)*(1+y),np.cos(angle)*(x+2)]])
    close(c.expectation_jacobian({a:x,b:y},[q.Z(0),q.X(0)]),expected)
    assert c.parameters==(a,b)

@pytest.mark.parametrize("seed",range(24))
def test_observable_embedding_disjoint_tensor(seed):
    rng=np.random.default_rng(seed+6606);wires=tuple(map(int,rng.choice(4,2,replace=False)))
    v=state(4,seed);r=q.Result(v)
    H=q.Observable({"YX":.8,"IZ":-.2,"II":.3})
    expected={}
    for label,coef in {"YX":.8,"IZ":-.2,"II":.3}.items():
        axes=["I"]*4
        for i,w in enumerate(wires):axes[3-w]=label[1-i]
        expected["".join(axes)]=coef
    M=sum(coef*dense(label) for label,coef in expected.items())
    close(r.math.expectation(H.on(wires,width=4)),np.vdot(v,M@v).real)
    P=q.Y(wires[0])@q.X(wires[1])
    label=["I"]*4;label[3-wires[0]]="Y";label[3-wires[1]]="X"
    close(r.math.expectation(P),np.vdot(v,dense("".join(label))@v).real)

@pytest.mark.parametrize("seed",range(12))
def test_semantic_sentinels_detect_wrong_results(seed):
    # These finite sentinels are not an automated mutation score for all code.
    v=state(2,seed+7707);r=q.Result(v)
    label="YI";correct=np.vdot(v,dense(label)@v).real
    for wrong in (-correct,np.vdot(v,dense("IY")@v).real):
        assert abs(correct-wrong)>1e-8
        assert r.test.expectation(label,float(wrong)).status=="FAIL"
    c=q.bell()
    good=c.run();bad=c.copy().z(0).run()
    close(list(good.math.probabilities().values()),list(bad.math.probabilities().values()))
    contract=c.contract(expectations={q.X(0)@q.X(1):1})
    contract.verify(good).require()
    assert contract.verify(bad).status=="FAIL"

def test_failure_preflight_and_phase_semantics(monkeypatch):
    c=q.Circuit(2).h(0);before=c.to_qiskit()
    with pytest.raises(q.UnsupportedOperation):
        c.evolve(q.X(0)+q.Z(0),time=.5)
    assert c.to_qiskit()==before
    t=q.Circuit.parameter("t");s=q.Circuit.symbolic(2).u(t,.2,.3,0)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**kw:pytest.fail("invalid input executed"))
    with pytest.raises(q.UnsupportedOperation):
        s.expectation_jacobian({t:.1},[q.Z(0)])
    with pytest.raises(q.ResourceLimit):
        q.Circuit.symbolic(1).ry(t,0).expectation_jacobian({t:.1},[q.Z(0)],max_bytes=1)
