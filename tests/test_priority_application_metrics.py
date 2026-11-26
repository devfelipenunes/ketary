from research.priority_application_metrics import run
from research.circuit_rewrite_ladder import metrics

def test_application_metrics():
    report=run(reps=2)
    assert len(report["rows"])==9
    for row in report["rows"]:
        assert set(row["paths"])=={"sdk","native"}
        for path in row["paths"].values():
            assert len(path["build"]["raw_ms"])==len(path["run"]["raw_ms"])==2
            assert path["basis_gates"]>=0

def test_repeated_ast_metrics():
    report=metrics("c.h(0)\nc.h(0)\n")
    assert report["duplicate_ast_groups"]>0
    assert report["duplicate_ast_excess"]>0
    assert metrics("c.h(0)\nc.x(1)\n")["duplicate_ast_groups"]==0
