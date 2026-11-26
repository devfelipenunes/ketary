import numpy as np
import pytest
from research.alpha_study_oracles import variational,phase_witness,evolution,VARIANTS

@pytest.mark.parametrize("variant",["A","B"])
def test_variational_scoring(variant):
    a,b=VARIANTS[variant]
    assert variational(variant)==pytest.approx(-np.hypot(2*a,b),abs=1e-12)

def test_relative_phase_scoring():
    a,b=phase_witness()
    np.testing.assert_allclose(abs(a)**2,abs(b)**2,atol=1e-12)
    assert abs(np.vdot(a,b))<1e-12
    np.testing.assert_allclose(np.vdot(a,a[::-1]),1.,atol=1e-12)
    np.testing.assert_allclose(np.vdot(b,b[::-1]),-1.,atol=1e-12)

@pytest.mark.parametrize("variant",["A","B"])
def test_evolution_scoring(variant):
    a,b=evolution(variant),evolution(variant,True)
    np.testing.assert_allclose(np.linalg.norm(a),1.,atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(b),1.,atol=1e-12)
    assert not np.allclose(a,b)
