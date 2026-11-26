import itertools
import pytest
import ketary as q


def test_alignment_between_different_gate_counts():
    a=q.Circuit(2).h(0).cx(0,1)
    b=q.Circuit(2).x(1).x(1).h(0).cx(0,1)
    r=a.debug.compare_checkpoints(b,[(0,0),(0,2),(1,3),(2,4)])
    assert r["status"]=="PASS" and len(r["checks"])==4
    assert a.debug.compare(b).check.status=="UNSUPPORTED"
    r=a.debug.compare_checkpoints(b.z(0),[(1,3),(2,5)])
    assert r["status"]=="FAIL" and r["checks"][-1]["reference_index"]==5
    assert a.debug.compare_checkpoints(b,[(2,4)],max_steps=2)["status"]=="UNSUPPORTED"
    assert a.debug.compare_checkpoints(q.Circuit(1),[(0,0)])["status"]=="UNSUPPORTED"
    assert a.debug.compare_checkpoints(b,[(0,0)],max_bytes=1)["status"]=="UNSUPPORTED"


def test_invalid_alignment_preflight(monkeypatch):
    a=q.bell()
    b=a.copy()
    monkeypatch.setattr(type(a.debug),"checkpoint",lambda *a,**k:pytest.fail("unexpected simulation"))
    for pairs in ([],[(0,0),(0,0)],[(1,1),(0,2)],[(0,)],[(0,0,0)],[(3,0)],itertools.repeat((0,0))):
        with pytest.raises(ValueError):
            a.debug.compare_checkpoints(b,pairs)
    with pytest.raises(TypeError):
        a.debug.compare_checkpoints(None,[(0,0)])
    with pytest.raises(ValueError):
        a.debug.compare_checkpoints(b,[(0,0)],ignore_global_phase=1)


@pytest.mark.parametrize("n",[1,2,3,4])
def test_simon_recovery_all_nonzero_secrets(n):
    for mask in range(1,1<<n):
        rows=[format(y,f"0{n}b") for y in range(1<<n) if (y&mask).bit_count()%2==0]
        assert q.recover_simon(rows,n)==format(mask,f"0{n}b")


def test_simon_recovery_bounds():
    assert q.recover_simon(["000","000"],3) is None
    with pytest.raises(ValueError):
        q.recover_simon(["01","10"],2)
    with pytest.raises(ValueError):
        q.recover_simon(["02"],2)
    with pytest.raises(q.ResourceLimit):
        q.recover_simon([],11)
    with pytest.raises(q.ResourceLimit):
        q.recover_simon(itertools.repeat("00"),2)
