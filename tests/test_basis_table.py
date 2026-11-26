import itertools
import pytest
import ketary as q

def test_table_prefix_and_explicit_order(monkeypatch):
    r=q.bell().run()
    def fail(*a,**k): raise AssertionError("unexpected circuit execution")
    monkeypatch.setattr(q.Circuit,"run",fail)
    lines=r.math.table(max_rows=2).splitlines()
    assert lines[0]=="basis | amplitude | probability"
    assert lines[1].startswith("00 |")
    assert lines[2].startswith("01 |")
    assert lines[3]=="... 2 basis rows omitted"
    lines=r.math.table(["11","00"]).splitlines()
    assert lines[1].startswith("11 |") and lines[2].startswith("00 |")
    assert len(lines)==3

def test_table_limits_and_invalid_labels():
    r=q.bell().run()
    with pytest.raises(q.ResourceLimit): r.math.table(itertools.repeat("00"),max_rows=2)
    with pytest.raises(ValueError): r.math.table(["02"])
    with pytest.raises(ValueError): r.math.table("00")
    with pytest.raises(ValueError): r.math.table(max_rows=0)
