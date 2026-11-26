from research.wave1_dynamic_protocols import run

def test_matched_protocol_diagnostic():
    report=run(reps=2)
    assert len(report["rows"])==10
    for row in report["rows"]:
        assert set(row["paths"])=={"sdk","native"}
        for path in row["paths"].values():
            assert len(path["build"]["raw_ms"])==len(path["run"]["raw_ms"])==len(path["counts"])==2
            assert all(sum(record["values"].values())==row["shots"] for record in path["counts"])
