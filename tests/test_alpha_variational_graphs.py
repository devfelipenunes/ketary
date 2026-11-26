"""Authored complete variational workflows; independent dense objective oracles."""
import numpy as np
import pytest
from scipy.optimize import minimize, minimize_scalar
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
import ketary as q


@pytest.mark.parametrize("edges", [
    ((0, 1, 0.7), (1, 2, 1.3)),
    ((0, 1, 0.7), (1, 2, 1.3), (0, 2, 0.4)),
])
def test_weighted_maxcut_workflow(edges):
    n = 3
    g, b = q.Circuit.parameter_vector("a", 2)
    obs = sum((w/2*(q.Z(i) @ q.Z(j) - q.I()) for i,j,w in edges), q.I()*0)
    sdk = q.Circuit.symbolic(n).h(range(n)).evolve(obs, time=g).rx(2*b, range(n))
    ng, nb = Parameter("gamma"), Parameter("beta")
    native = QuantumCircuit(n)
    native.h(range(n))
    for i,j,w in edges:
        native.rzz(w*ng, i,j)
    native.global_phase = sum(w for _,_,w in edges)*ng/2
    native.rx(2*nb, range(n))
    diagonal = np.array([-sum(w for i,j,w in edges if ((k>>i)&1) != ((k>>j)&1))
                         for k in range(1<<n)])
    ground = min(diagonal)
    histories = {"sdk": [], "native": []}

    def energy(route, point):
        gamma,beta = map(float, point)
        if route == "sdk":
            result = sdk.bind({g:gamma,b:beta}).run()
            value = result.math.expectation(obs)
            np.testing.assert_allclose(value, np.dot(abs(result.math.statevector())**2, diagonal), atol=1e-9)
        else:
            result = Statevector.from_instruction(native.assign_parameters({ng:gamma,nb:beta}))
            value = float(np.dot(abs(result.data)**2,diagonal))
        histories[route].append(value)
        return value

    for point in ((.13,-.2),(.7,-.4),(1.1,.5)):
        gamma,beta = point
        np.testing.assert_allclose(sdk.bind({g:gamma,b:beta}).run().math.statevector(),
            Statevector.from_instruction(native.assign_parameters({ng:gamma,nb:beta})).data, atol=1e-9,rtol=0)
        np.testing.assert_allclose(energy("sdk",point),energy("native",point),atol=1e-9,rtol=0)
    results = {}
    for route in histories:
        results[route] = minimize(lambda x:energy(route,x), [.5,-.3], method="Powell",
                                  bounds=[(0.,2.),(-np.pi/4,0.)],
                                  options={"xtol":1e-8,"ftol":1e-9})
        assert results[route].success
        assert ground-1e-9 <= results[route].fun < np.mean(diagonal)-1e-3
    np.testing.assert_allclose(results["sdk"].fun,results["native"].fun,atol=1e-7,rtol=0)
    point = results["sdk"].x
    snapshot = sdk.bind({g:float(point[0]),b:float(point[1])}).run()
    q.Contract(n, expectations={obs:float(results["native"].fun)},atol=1e-7).verify(snapshot).require()
    assert len(histories["sdk"]) > 3


def test_excited_state_penalty_workflow():
    # Explicitly restricted to the even-parity subspace, not general VQD.
    Z = np.diag([1.,-1.]); X = np.array([[0.,1.],[1.,0.]])
    H = .5*(np.kron(Z,np.eye(2))+np.kron(np.eye(2),Z))+.7*np.kron(X,X)
    obs = .5*(q.Z(0)+q.Z(1))+.7*(q.X(0)@q.X(1))
    basis = np.array([0,3])
    eigenvalues,eigenvectors = np.linalg.eigh(H[np.ix_(basis,basis)])
    ground = np.zeros(4,complex);ground[basis] = eigenvectors[:,0]
    p = q.Circuit.parameter("theta")
    sdk = q.Circuit.symbolic(2).ry(p,0).cx(0,1)
    np_ = Parameter("theta"); native = QuantumCircuit(2)
    native.ry(np_,0);native.cx(0,1)
    penalty = 4.
    def evaluate(route, t):
        if route == "sdk":
            result = sdk.bind({p:float(t)}).run()
            state = result.math.statevector()
            value = result.math.expectation(obs)
        else:
            state = Statevector.from_instruction(native.assign_parameters({np_:float(t)})).data
            value = float(np.vdot(state,H@state).real)
        return value+penalty*abs(np.vdot(ground,state))**2
    for t in np.linspace(-2.,2.,7):
        np.testing.assert_allclose(evaluate("sdk",t),evaluate("native",t),atol=1e-9,rtol=0)
    for route in ("sdk","native"):
        result = minimize_scalar(lambda t:evaluate(route,t),bounds=(-np.pi,np.pi),method="bounded")
        assert result.success
        assert abs(result.fun-eigenvalues[1])<1e-7
        state = sdk.bind({p:float(result.x)}).run()
        q.Contract(2,expectations={obs:float(eigenvalues[1])},atol=1e-7).verify(state).require()
        assert abs(np.vdot(ground,state.math.statevector()))**2<1e-7
