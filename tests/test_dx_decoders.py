import pytest
import ketary as q

@pytest.mark.parametrize("mask",["1","101","1100","0011"])
def test_bv_decode(mask):
    result=q.decode_bernstein_vazirani(q.bernstein_vazirani(mask).run())
    assert result["label"]==mask and result["status"]=="PASS"
    assert result["peak_probability"]==pytest.approx(1)

@pytest.mark.parametrize("label",range(8))
def test_qpe_decode(label):
    result=q.decode_phase_estimation(q.phase_estimation(label/8,precision=3).run(),precision=3)
    assert result["phase"]==label/8 and result["status"]=="PASS"
    assert result["peak_probability"]==pytest.approx(1)

def test_ties_and_invalid_width():
    result=q.Circuit(2).h(0).run()
    assert q.decode_bernstein_vazirani(result)["status"]=="INCONCLUSIVE"
    assert q.decode_phase_estimation(result,precision=1)["phase"] is None
    with pytest.raises(ValueError):
        q.decode_phase_estimation(result,precision=2)
    with pytest.raises(TypeError):
        q.decode_bernstein_vazirani(q.bell())

def test_teleportation_decoder_schema():
    s=q.ShotResult(10,3,1,(("000",3),("100",7)),((1,2,2),))
    d=q.decode_teleportation(s)
    assert d["counts"]=={"0":3,"1":7}
    assert d["probabilities"]=={"0":.3,"1":.7}
    with pytest.raises(ValueError):
        q.decode_teleportation(q.ShotResult(10,3,1,(("000",10),)))
