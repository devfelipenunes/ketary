import numpy as np
from benchmark import mixed_workload, build, execute

def test_mixed_workload_equivalence():
    ops=mixed_workload(4,128)
    assert ops==mixed_workload(4,128)
    assert any(g in ("rx","ry","rz") for g,_ in ops)
    a,b=build(4,ops,"native"),build(4,ops,"sdk")
    assert a==b.to_qiskit()
    np.testing.assert_allclose(execute(a,"native"),execute(b,"sdk"),atol=1e-12)
