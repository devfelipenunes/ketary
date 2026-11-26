"""Native variational templates, explicit ordered parameters and resource bounds."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.circuit.library import real_amplitudes, efficient_su2, n_local
from qiskit.quantum_info import Operator


@pytest.mark.parametrize("n,reps",[(2,1),(3,2),(4,3),(5,1)])
@pytest.mark.parametrize("rotations",[("ry",),("ry","rz")])
def test_native_library_equivalence(n,reps,rotations):
    c=q.ansatz(n,reps=reps,rotations=rotations)
    native=(real_amplitudes(n,entanglement="linear",reps=reps) if rotations==("ry",)
            else efficient_su2(n,entanglement="linear",reps=reps))
    values=np.linspace(-.8,.9,len(native.parameters))
    expected=native.assign_parameters(values)
    actual=c.bind(values)
    assert len(c.parameters)==len(values)
    assert actual.parameters==()
    np.testing.assert_allclose(Operator(actual.to_qiskit()).data,Operator(expected).data,atol=1e-12,rtol=0)
    assert len(c.parameters)==len(values)


@pytest.mark.parametrize("topology",["linear","reverse_linear","circular","full"])
def test_native_order_and_prefix(topology):
    c=q.ansatz(4,rotations=("rx","rz","ry"),entanglement=topology,reps=2,prefix="w")
    native=n_local(4,rotation_blocks=["rx","rz","ry"],entanglement_blocks="cx",
                   entanglement=topology,reps=2,parameter_prefix="w")
    assert [p.name for p in c.parameters]==[p.name for p in native.parameters]
    values=np.linspace(.1,.9,len(c.parameters))
    assert c.bind(values).to_qiskit()==native.assign_parameters(values)


def test_parameter_vector_identity_and_ordered_binding():
    v=q.Circuit.parameter_vector("theta",12)
    assert isinstance(v,tuple)
    assert len(set(v))==12
    assert v!=q.Circuit.parameter_vector("theta",12)
    c=q.Circuit.symbolic(3).ry(v[:3],range(3)).rz(v[3:6],range(3))
    values=[.1,.2,.3,.4,.5,.6]
    assert c.bind(iter(values)).to_qiskit()==c.bind(dict(zip(c.parameters,values))).to_qiskit()
    assert c.bind(values).to_qiskit()==c.bind(**dict(zip((p.name for p in c.parameters),values))).to_qiskit()


def test_composition_and_shared_parameter_conflict():
    a=q.ansatz(2,prefix="a")
    b=q.ansatz(2,prefix="b",rotations=("ry","rz"))
    c=q.Circuit.symbolic(4).apply(a,wires=[3,0]).apply(b,wires=[1,2]).apply(a,wires=[0,1])
    assert set(c.parameters)==set(a.parameters)|set(b.parameters)
    vals=[.2]*len(c.parameters)
    expected=c.to_qiskit().assign_parameters(vals)
    assert c.bind(vals).to_qiskit()==expected
    before=c.to_qiskit()
    with pytest.raises(ValueError,match="conflicting parameter"):
        c.apply(q.ansatz(2,prefix="a"),wires=[0,1])
    assert c.to_qiskit()==before


@pytest.mark.parametrize("kwargs",[
    {"n":1},{"n":True},{"n":63},{"n":4,"reps":0},{"n":4,"reps":65},
    {"n":4,"rotations":[]},{"n":4,"rotations":"ry"},{"n":4,"rotations":["h"]},
    {"n":4,"rotations":{"ry"}},{"n":4,"rotations":itertools.repeat("ry")},
    {"n":4,"entanglement":"hardware"},{"n":4,"prefix":""},
    {"n":62,"reps":64,"entanglement":"full"},
])
def test_invalid_ansatz_preflight(kwargs,monkeypatch):
    def forbidden(*a,**k):
        pytest.fail("native factory called before preflight")
    monkeypatch.setattr(q.Circuit,"_native_ansatz",forbidden)
    with pytest.raises(ValueError):
        q.ansatz(**kwargs)


@pytest.mark.parametrize("values",[[.1], [0.1]*5,[.1,.2,.3,float("nan")], {0.1,0.2}, "1234"])
def test_ordered_binding_rejects_invalid_values(values):
    c=q.ansatz(2)
    before=c.to_qiskit()
    with pytest.raises((TypeError,ValueError)):
        c.bind(values)
    assert c.to_qiskit()==before


def test_no_implicit_execution_and_bound_only_modes():
    c=q.ansatz(4)
    with pytest.raises(q.UnsupportedOperation):
        c.run()
    with pytest.raises(q.UnsupportedOperation):
        c.to_json()
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit(4).apply(c)
    with pytest.raises(q.ResourceLimit):
        q.Circuit.parameter_vector("v",4097)
    with pytest.raises(ValueError):
        q.Circuit.parameter_vector("",2)
    assert c.bind([0.]*len(c.parameters)).run().math.probability("0000")==pytest.approx(1)
