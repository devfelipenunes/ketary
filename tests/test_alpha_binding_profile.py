from research.alpha_binding_profile import run

def test_alpha_binding_profile_smoke():
    rows=run(1101,1)
    assert rows
