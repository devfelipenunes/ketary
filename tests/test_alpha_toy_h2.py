import numpy as np
import pytest
from research.alpha_toy_h2 import matrix,expected_state,ketary_path,native_path,evaluate


def test_toy_h2_exact_sectors():
    h=matrix()
    expected=np.array([[-.23,0,0,.36],[0,-1.27,0,0],[0,0,-1.07,0],[.36,0,0,-1.63]])
    # ZI acts on the high wire, IZ on the low wire.
    expected[1,1],expected[2,2]=-1.07,-1.27
    np.testing.assert_allclose(h,expected,atol=1e-12,rtol=0)
    assert np.linalg.eigvalsh(h)[0]==pytest.approx(-.93-np.hypot(.7,.36),abs=1e-12)
    for build in (ketary_path,native_path):
        _,objective,state=build()
        for theta in (-2.3,0.,.6,2.8):
            np.testing.assert_allclose(state(theta),expected_state(theta),atol=1e-9,rtol=0)
            assert objective(theta)==pytest.approx(-.93+.7*np.cos(theta)+.36*np.sin(theta),abs=1e-9)


def test_toy_h2_optimizer():
    row=evaluate(1101,1)
    assert len(row["paths"])==2
    for path in row["paths"].values():
        assert path["histories"][0]["energy"]==pytest.approx(row["ground"],abs=1e-8)
