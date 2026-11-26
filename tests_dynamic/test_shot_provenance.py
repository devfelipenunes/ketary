import ketary as q

def test_measurement_provenance():
    c=q.Circuit.classical(2,2).x(0).measure(0,1)
    r=c.run_shots(shots=8,seed=2)
    assert r.counts=={"10":8}
    assert r.measurements==((2,0,1),)
    assert r.measured_bits==(1,)
    assert r.backend=="qiskit-aer/statevector"
    assert r.backend_version!="unknown"
