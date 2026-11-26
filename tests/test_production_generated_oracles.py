"""1,000 deterministic generated independent mathematical cases.

Replay a failure with its pytest node ID. No native Qiskit oracle is used for
the expected matrices. These are generated cases, not unique applications or
a universal accuracy certificate.
"""
import numpy as np
import pytest
import ketary as q

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.diag([1.,-1.]).astype(complex)
H=(X+Z)/np.sqrt(2)
PAULIS={"I":I,"X":X,"Y":Y,"Z":Z}

def pauli(label):
    out=np.ones((1,1),complex)
    for axis in label:out=np.kron(out,PAULIS[axis])
    return out

def embed(M,n,w):
    out=np.ones((1,1),complex)
    for wire in reversed(range(n)):out=np.kron(out,M if wire==w else I)
    return out

def normalized(rng,n):
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    return v/np.linalg.norm(v)

@pytest.mark.parametrize("seed",range(250))
def test_generated_state_math(seed):
    rng=np.random.default_rng(24001+seed)
    n=int(rng.integers(1,5));v=normalized(rng,n)
    # Explicitly include near-basis/near-product and high imbalance cases.
    if seed%5==0:
        v[1:]*=10.**(-int(rng.integers(4,12)))
        v/=np.linalg.norm(v)
    r=q.Result(v)
    label="".join(rng.choice(list(PAULIS),size=n))
    P=pauli(label)
    e=np.vdot(v,P@v).real
    np.testing.assert_allclose(r.math.expectation(label),e,atol=1e-9,rtol=0)
    np.testing.assert_allclose(r.math.variance(label),1-e*e,atol=1e-9,rtol=0)
    probabilities=[r.math.probability(format(j,f"0{n}b")) for j in range(1<<n)]
    np.testing.assert_allclose(probabilities,abs(v)**2,atol=1e-9,rtol=0)
    assert abs(sum(probabilities)-1)<1e-9
    wires=list(map(int,rng.permutation(n)[:int(rng.integers(1,n+1))]))
    other=[i for i in range(n) if i not in wires]
    # Explicit bit-index reduction: first selected wire is output MSB.
    A=np.zeros((1<<len(wires),1<<len(other)),complex)
    for j,z in enumerate(v):
        a=sum(((j>>w)&1)<<(len(wires)-1-i) for i,w in enumerate(wires))
        b=sum(((j>>w)&1)<<i for i,w in enumerate(other))
        A[a,b]=z
    rho=A@A.conj().T
    got=r.math.density_matrix(wires)
    np.testing.assert_allclose(got,rho,atol=1e-9,rtol=0)
    np.testing.assert_allclose(r.math.purity(wires),np.trace(rho@rho).real,atol=1e-9,rtol=0)
    assert np.linalg.eigvalsh(got).min()>=-1e-9

@pytest.mark.parametrize("seed",range(250))
def test_generated_ordered_unitaries(seed):
    rng=np.random.default_rng(25001+seed)
    n=int(rng.integers(1,5));v=normalized(rng,n)
    c=q.Circuit(n);U=np.eye(1<<n,dtype=complex)
    for _ in range(int(rng.integers(5,19))):
        w=int(rng.integers(n));kind=int(rng.integers(6));theta=float(rng.uniform(-4,4))
        if kind==0:c.h(w);G=embed(H,n,w)
        elif kind==1:c.x(w);G=embed(X,n,w)
        elif kind==2:c.ry(theta,w);G=embed(np.cos(theta/2)*I-1j*np.sin(theta/2)*Y,n,w)
        elif kind==3:c.rz(theta,w);G=embed(np.cos(theta/2)*I-1j*np.sin(theta/2)*Z,n,w)
        elif kind==4 and n>1:
            target=(w+int(rng.integers(1,n)))%n;c.cx(w,target)
            G=np.zeros_like(U)
            for j in range(1<<n):G[j^(((j>>w)&1)<<target),j]=1
        else:c.p(theta,w);G=embed(np.diag([1,np.exp(1j*theta)]),n,w)
        U=G@U
    phase=float(rng.uniform(-3,3))
    c.evolve(q.I(n-1),time=phase);U=np.exp(-1j*phase)*U
    got=c.run(initial_state=v).math.statevector()
    np.testing.assert_allclose(got,U@v,atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.inverse().run(initial_state=got).math.statevector(),v,atol=1e-9,rtol=0)
    replay=q.Circuit.from_json(c.to_json())
    np.testing.assert_allclose(replay.run(initial_state=v).math.statevector(),got,atol=1e-9,rtol=0)

@pytest.mark.parametrize("seed",range(250))
def test_generated_pauli_sum_algebra(seed):
    rng=np.random.default_rng(26001+seed)
    n=int(rng.integers(1,5))
    def build():
        terms={}
        for _ in range(int(rng.integers(2,10))):
            label="".join(rng.choice(list(PAULIS),size=n))
            terms[label]=float(rng.uniform(-2,2))
        matrix=sum((coef*pauli(p) for p,coef in terms.items()),np.zeros((1<<n,1<<n),complex))
        return q.Observable(terms),matrix
    a,A=build();b,B=build();v=normalized(rng,n);r=q.Result(v)
    AB=a.product(b);C=a.commutator(b);D=a.anticommutator(b)
    np.testing.assert_allclose(AB.to_matrix(),A@B,atol=1e-9,rtol=0)
    np.testing.assert_allclose(C.to_matrix(),A@B-B@A,atol=1e-9,rtol=0)
    np.testing.assert_allclose(D.to_qiskit().to_matrix(),A@B+B@A,atol=1e-9,rtol=0)
    np.testing.assert_allclose(r.math.expectation_complex(AB),np.vdot(v,A@B@v),atol=1e-9,rtol=0)
    e=np.vdot(v,A@v).real
    np.testing.assert_allclose(r.math.expectation(a),e,atol=1e-9,rtol=0)
    np.testing.assert_allclose(r.math.variance(a),np.linalg.norm(A@v-e*v)**2,atol=1e-9,rtol=0)

@pytest.mark.parametrize("seed",range(250))
def test_generated_nonlinear_geometry(seed):
    rng=np.random.default_rng(27001+seed)
    a,b=q.Circuit.parameter_vector("v",2)
    x,y=rng.uniform(-1.5,1.5,size=2)
    k,l,m=map(float,rng.uniform(-1.2,1.2,size=3))
    if seed%10==0:x=y=0.
    # theta=k*a^2+l*a*b+m*b; separate occurrences exercise shared parameters.
    c=q.Circuit.symbolic(1).ry(k*a*a,0).ry(l*a*b,0).ry(m*b,0)
    theta=k*x*x+l*x*y+m*y
    g=np.array([2*k*x+l*y,l*x+m]);curvature=np.array([[2*k,l],[l,0.]])
    s,t=np.sin(theta),np.cos(theta)
    want_j=np.array([t*g,-s*g])
    want_h=np.array([-s*np.outer(g,g)+t*curvature,-t*np.outer(g,g)-s*curvature])
    bindings={a:x,b:y};obs=[q.X(0),q.Z(0)]
    np.testing.assert_allclose(c.expectation_jacobian(bindings,obs),want_j,atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.expectation_hessian(bindings,obs),want_h,atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.quantum_geometric_tensor(bindings),np.outer(g,g)/4,atol=1e-9,rtol=0)
