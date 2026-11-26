"""Bounded dynamic branch trees with independent classical truth tables."""
import itertools
import pytest
import ketary as q
from qiskit import QuantumCircuit,QuantumRegister,ClassicalRegister

def build(a,b,depth,*,register_condition=False):
    raw=QuantumCircuit(QuantumRegister(3),ClassicalRegister(1,"a"),ClassicalRegister(1,"b"),ClassicalRegister(1,"out"))
    if a:raw.x(0)
    if b:raw.x(1)
    raw.measure([0,1],[0,1])
    outer=(raw.cregs[0],1) if register_condition else (raw.clbits[0],1)
    with raw.if_test(outer) as other:
        with raw.if_test((raw.clbits[1],1)) as inner:
            if depth==3:
                with raw.if_test((raw.clbits[0],1)):raw.x(2)
            else:raw.x(2)
        with inner:raw.z(2)
    with other:raw.x(2)
    raw.measure(2,2)
    return raw

@pytest.mark.parametrize("a,b",list(itertools.product([0,1],repeat=2)))
@pytest.mark.parametrize("depth",[2,3])
@pytest.mark.parametrize("register_condition",[False,True])
def test_nested_structure(a,b,depth,register_condition):
    raw=build(a,b,depth,register_condition=register_condition)
    c=q.Circuit.from_dynamic(raw)
    assert c.to_qiskit()==raw
    assert c.copy().to_qiskit()==raw
    raw.x(2)
    assert c.to_qiskit()!=raw

@pytest.mark.parametrize("a,b",list(itertools.product([0,1],repeat=2)))
@pytest.mark.parametrize("depth",[2,3])
@pytest.mark.parametrize("register_condition",[False,True])
def test_nested_truth_table(a,b,depth,register_condition):
    pytest.importorskip("qiskit_aer")
    c=q.Circuit.from_dynamic(build(a,b,depth,register_condition=register_condition))
    out=int(not a or b)
    result=c.run_shots(shots=16,seed=41)
    assert result.counts=={f"{out}{b}{a}":16}
    assert result.measured_bits==(0,1,2)
    assert result.num_clbits==3

def test_nested_depth_and_expanded_budget():
    raw=QuantumCircuit(1,1);raw.measure(0,0)
    with raw.if_test((raw.clbits[0],1)):
        with raw.if_test((raw.clbits[0],1)):
            with raw.if_test((raw.clbits[0],1)):
                with raw.if_test((raw.clbits[0],1)):raw.x(0)
    with pytest.raises(q.ResourceLimit,match="depth"):q.Circuit.from_dynamic(raw)
    raw=QuantumCircuit(1,1);raw.measure(0,0)
    with raw.if_test((raw.clbits[0],1)):
        with raw.if_test((raw.clbits[0],1)) as other:
            for _ in range(510):raw.x(0)
        with other:
            for _ in range(512):raw.z(0)
    with pytest.raises(q.ResourceLimit,match="expanded"):q.Circuit.from_dynamic(raw)

@pytest.mark.parametrize("kind",["measure","reset","loop"])
def test_nested_forbidden_leaves_even_in_unreachable_branch(kind):
    raw=QuantumCircuit(1,1);raw.measure(0,0)
    with raw.if_test((raw.clbits[0],1)):
        with raw.if_test((raw.clbits[0],1)):
            if kind=="measure":raw.measure(0,0)
            elif kind=="reset":raw.reset(0)
            else:
                with raw.for_loop(range(1)):raw.x(0)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.from_dynamic(raw)
