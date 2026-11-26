"""Bound expansion after caller iterable side effects, before native composition."""
import pytest
import ketary as q
from ketary import _adapter

def test_placement_generator_cannot_bypass_final_expansion_cap(monkeypatch):
    block = q.Circuit(1).x(0)
    target = q.Circuit(1).h(0)
    before = target.to_qiskit()
    def placements():
        for _ in range(400):
            yield (0,)
        for _ in range(250):
            block.x(0)
    def forbidden(*args,**kwargs):
        pytest.fail("native append before final expansion cap")
    monkeypatch.setattr(_adapter,"_append_bound_blocks",forbidden)
    with pytest.raises(q.ResourceLimit):
        target.apply_each(block,placements=placements())
    assert target.to_qiskit()==before
    assert len(block.to_qiskit().data)==251

def test_placement_generator_valid_final_source():
    block = q.Circuit(1).x(0)
    target = q.Circuit(2)
    def placements():
        yield (1,)
        yield (0,)
        block.z(0)
    target.apply_each(block,placements=placements())
    expected = q.Circuit(2).x(1).z(1).x(0).z(0)
    target.test.equivalent(expected).require()
