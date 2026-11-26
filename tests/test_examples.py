from examples.first_bell import main as first_bell
from examples.diagnose_phase import main as diagnose_phase

def test_first_bell_journey():
    result = first_bell()
    result.test.probability("00", 0.5).require()

def test_imported_phase_diagnosis_journey():
    check, trace = diagnose_phase()
    assert check.status == "FAIL"
    assert check.actual < 1e-12
    assert trace[-1].operation == "z"
