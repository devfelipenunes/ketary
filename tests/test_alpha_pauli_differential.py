"""Independent small dense matrix corpus for observable and state semantics."""
import itertools
import numpy as np
import pytest
import ketary as q

P = {
    "I":np.eye(2,dtype=complex),
    "X":np.array([[0,1],[1,0]],complex),
    "Y":np.array([[0,-1j],[1j,0]],complex),
    "Z":np.diag([1.,-1.]).astype(complex),
}

def dense(terms):
    n = len(next(iter(terms)))
    result = np.zeros((1<<n,1<<n),complex)
    for label,coef in terms.items():
        matrix = np.ones((1,1),complex)
        for axis in label:
            matrix = np.kron(matrix,P[axis])
        result += coef*matrix
    return result

@pytest.mark.parametrize("seed",[1101,2202,3303])
@pytest.mark.parametrize("n",[1,2,3,4])
def test_seeded_algebra(seed,n):
    rng = np.random.default_rng(seed)
    labels = ["".join(row) for row in itertools.product("IXYZ",repeat=n)]
    def terms():
        chosen = rng.choice(labels,size=min(len(labels),7),replace=False)
        return {str(label):float(value) for label,value in zip(chosen,rng.normal(size=len(chosen)),strict=True)}
    a,b = terms(),terms()
    A,B = dense(a),dense(b)
    x,y = q.Observable(a),q.Observable(b)
    np.testing.assert_allclose(x.product(y).to_matrix(),A@B,atol=1e-9,rtol=0)
    np.testing.assert_allclose(x.commutator(y).to_matrix(),A@B-B@A,atol=1e-9,rtol=0)
    np.testing.assert_allclose(x.anticommutator(y).to_qiskit().to_matrix(),A@B+B@A,atol=1e-9,rtol=0)
    np.testing.assert_allclose((x+y).to_qiskit().to_matrix(),A+B,atol=1e-9,rtol=0)
    vector = rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    vector /= np.linalg.norm(vector)
    state = q.Result(vector)
    expected = np.vdot(vector,A@vector)
    np.testing.assert_allclose(state.math.expectation(x),expected.real,atol=1e-9,rtol=0)
    np.testing.assert_allclose(state.math.observable_variance(x),np.linalg.norm(A@vector-expected*vector)**2,atol=1e-9,rtol=0)
    np.testing.assert_allclose(state.math.expectation_complex(x.product(y)),np.vdot(vector,A@B@vector),atol=1e-9,rtol=0)
    q.Contract(n,expectations={x:float(expected.real)}).verify(state).require()
    original = state.math.statevector()
    vector[:] = 0
    exported = state.math.statevector();exported[:] = 0
    np.testing.assert_array_equal(state.math.statevector(),original)

@pytest.mark.parametrize("wires",list(itertools.permutations(range(3),2)))
def test_ordered_embedding(wires):
    local = {"XY":.8,"ZI":-.3,"II":.2}
    global_terms = {}
    for label,coef in local.items():
        full = ["I"]*3
        for bit,wire in enumerate(wires):
            full[2-wire] = label[1-bit]
        global_terms["".join(full)] = coef
    actual = q.Observable(local).on(wires,width=3)
    np.testing.assert_allclose(actual.to_qiskit().to_matrix(),dense(global_terms),atol=1e-9,rtol=0)

def test_disjoint_and_invalid_support():
    a,b = q.X(2)+.3*q.Y(2),q.Z(0)-.2*q.I()
    expected = dense({"XII":1.,"YII":.3})@dense({"IIZ":1.,"III":-.2})
    np.testing.assert_allclose((a@b).to_qiskit().to_matrix(),expected,atol=1e-9,rtol=0)
    with pytest.raises(ValueError):
        a@q.Z(2)
    with pytest.raises(ValueError):
        q.Observable({"XY":1.}).on([0,0],width=3)
    with pytest.raises(ValueError):
        q.Observable({"Z":float("nan")})
