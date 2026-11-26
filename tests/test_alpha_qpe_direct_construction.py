import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Statevector
from research.alpha_qpe_power_profile import direct_inverse_qft,legacy_composed

@pytest.mark.parametrize("m",[1,2,3,5,8,12])
@pytest.mark.parametrize("phase",[0.,.375,.237,np.nextafter(1.,0.)])
def test_direct_inverse_qft_matches_existing_structure(m,phase):
    actual=direct_inverse_qft(phase,m)
    assert actual==q.phase_estimation(phase,precision=m).to_qiskit()==legacy_composed(phase,m)

def test_twelve_bit_exact_grid_phase():
    m=12;p=.375
    v=Statevector.from_instruction(q.phase_estimation(p,precision=m).to_qiskit()).data
    expected=np.zeros(1<<(m+1),dtype=complex)
    expected[(1<<m)+int(p*(1<<m))]=1.
    np.testing.assert_allclose(v,expected,atol=1e-9,rtol=0)
