from research.closure_qec_metrics import evaluate
import pytest

@pytest.mark.parametrize("family,arg",[("bit",0.),("bit",.08),("bit",1.),("phase",0.),("phase",.08),("phase",1.),("syndrome",None),("syndrome",0),("syndrome",1),("syndrome",2)])
def test_matched_qec_metrics(family,arg):
    row=evaluate(family,.83,-1.17,arg,reps=2)
    assert set(row["paths"])=={"sdk","native"}
    assert all(len(path["run"]["raw_ms"])==2 for path in row["paths"].values())
    if family!="syndrome":
        assert row["paths"]["sdk"]["logical_fidelity"]==pytest.approx(row["paths"]["native"]["logical_fidelity"])
        if arg==1.:assert row["paths"]["sdk"]["logical_fidelity"]<.5
