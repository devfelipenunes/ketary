from research.alpha_synthesis_depth import run

def test_candidate_synthesis_depth():
    rows=run(1101,1)
    assert len(rows)==6
    for row in rows[:3]:
        assert row["paths"]["candidate"]["common_cx"]==2
        assert row["paths"]["baseline"]["common_cx"]==4
