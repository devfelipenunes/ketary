"""Executable authored reference workflows, not an independent usability study."""
import numpy as np
import pytest
from scipy.optimize import minimize, minimize_scalar
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
import ketary as q

ATOL = 1e-9

def vqe():
    # Noncommuting spin Hamiltonian; the even subspace contains its ground state.
    Z = np.diag([1., -1.])
    X = np.array([[0., 1.], [1., 0.]])
    H = .5 * (np.kron(np.eye(2), Z) + np.kron(Z, np.eye(2))) + .7 * np.kron(X, X)
    obs = .5 * (q.Z(0) + q.Z(1)) + .7 * (q.X(0) @ q.X(1))
    p = q.Circuit.parameter("theta")
    layer = q.Circuit.symbolic(2).ry(p, 0).cx(0, 1)
    circuit = q.Circuit.symbolic(2).apply(layer)
    native_p = Parameter("theta")
    native = QuantumCircuit(2)
    native.ry(native_p, 0)
    native.cx(0, 1)
    histories = {"ketary": [], "qiskit": []}

    def evaluate(route, theta):
        if route == "ketary":
            value = circuit.bind({p: theta}).run().math.expectation(obs)
        else:
            state = Statevector.from_instruction(native.assign_parameters({native_p: theta})).data
            value = float(np.vdot(state, H @ state).real)
        histories[route].append((float(theta), value))
        return value

    for theta in (-2.1, -.3, 0., .8, 2.4):
        np.testing.assert_allclose(evaluate("ketary", theta), evaluate("qiskit", theta), atol=ATOL, rtol=0)
        expected = -np.sin(theta) + .7 * np.cos(theta)
        np.testing.assert_allclose(circuit.expectation_jacobian({p: theta}, [obs]), [[expected]], atol=ATOL, rtol=0)
    results = {route: minimize_scalar(lambda t: evaluate(route, t), bounds=(0., 2*np.pi), method="bounded", options={"xatol": 1e-11}) for route in histories}
    ground = float(np.linalg.eigvalsh(H)[0])
    for result in results.values():
        assert result.success
        assert abs(result.fun - ground) < 1e-8
    result = circuit.bind({p: float(results["ketary"].x)}).run()
    q.Contract(2, expectations={obs: ground}, atol=1e-8).verify(result).require()
    assert result.math.observable_variance(obs) < 1e-8
    return histories, ground

def qaoa(weight):
    # A weighted edge is an exactly soluble QAOA control; no unweighted
    # surrogate observable. Minimize negative weighted MaxCut.
    g, b = q.Circuit.parameter_vector("angle", 2)
    cost = .5 * weight * ((q.Z(0) @ q.Z(1)) - q.I())
    circuit = q.Circuit.symbolic(2).h(range(2)).evolve(cost, time=g).rx(2*b, range(2))
    ng, nb = Parameter("gamma"), Parameter("beta")
    native = QuantumCircuit(2)
    native.h(range(2))
    native.rzz(weight*ng, 0, 1)
    native.global_phase = weight*ng/2
    native.rx(2*nb, range(2))
    diagonal = np.array([0., -weight, -weight, 0.])
    histories = {"ketary": [], "qiskit": []}

    def evaluate(route, point):
        gamma, beta = map(float, point)
        if route == "ketary":
            value = circuit.bind({g: gamma, b: beta}).run().math.expectation(cost)
        else:
            state = Statevector.from_instruction(native.assign_parameters({ng: gamma, nb: beta})).data
            value = float(np.dot(abs(state)**2, diagonal))
        histories[route].append((gamma, beta, value))
        return value

    for point in ((.12, .21), (.5, -.2), (-.7, .8)):
        np.testing.assert_allclose(evaluate("ketary", point), evaluate("qiskit", point), atol=ATOL, rtol=0)
    # Start away from the optimum; same optimizer and box for each route.
    bounds = [(0., np.pi/weight), (-np.pi/4, 0.)]
    results = {route: minimize(lambda x: evaluate(route, x), [.3/weight, -.2], method="Powell", bounds=bounds, options={"xtol": 1e-9, "ftol": 1e-10}) for route in histories}
    for result in results.values():
        assert result.success
        assert abs(result.fun + weight) < 1e-7
    gamma, beta = map(float, results["ketary"].x)
    snapshot = circuit.bind({g: gamma, b: beta}).run()
    q.Contract(2, expectations={cost: -weight}, atol=1e-7).verify(snapshot).require()
    assert abs(snapshot.math.probability("01") + snapshot.math.probability("10") - 1.) < 1e-7
    return histories

def test_alpha_vqe():
    vqe()

@pytest.mark.parametrize("weight", [.7, 1.7, 2.4])
def test_alpha_weighted_qaoa(weight):
    qaoa(weight)

if __name__ == "__main__":
    histories, ground = vqe()
    print("VQE ground:", ground, "evaluations:", {k: len(v) for k,v in histories.items()})
    print("QAOA evaluations:", {k: len(v) for k,v in qaoa(1.7).items()})
