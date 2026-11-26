from research.alpha_parity_profile import run

def test_alpha_parity_profile_smoke():
    rows=run(1101,1)
    assert rows
