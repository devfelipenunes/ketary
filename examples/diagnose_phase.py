"""Show why identical measurement probabilities do not imply equal states."""
import numpy as np
from qiskit import QuantumCircuit
import ketary as q

def main():
    raw = QuantumCircuit(2)
    raw.h(0)
    raw.cx(0, 1)
    raw.z(0)
    circuit = q.from_qiskit(raw)
    expected = q.bell().run()
    observed = circuit.run()
    np.testing.assert_allclose(list(expected.math.probabilities().values()),
                               list(observed.math.probabilities().values()), atol=1e-12)
    check = observed.test.fidelity(expected)
    assert check.status == "FAIL"
    trace = circuit.debug.trace()
    assert trace[-2].result.test.fidelity(expected).status == "PASS"
    assert trace[-1].result.test.fidelity(expected).status == "FAIL"
    print("Identical probabilities; fidelity:", check.actual)
    print("Observed divergence at the last step:", trace[-1].operation)
    return check, trace

if __name__ == "__main__":
    main()
