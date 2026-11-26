from research.dedicated_performance_host import command_plan,preflight,ROOT
import pytest

def test_host_plan_covers_all_diagnostics_without_execution():
    plan=command_plan()
    names=[name for name,_,_ in plan]
    assert len(names)==len(set(names))==13
    assert set(names)=={"baseline","fluent","pauli","batches","trace-index",
                       "singleton-tails","native-finite","simd","cold-pool",
                       "warm-pool","suffix","trace-terminal","memory"}
    assert all("--output" in args or stdout=="benchmark.json" for _,args,stdout in plan)

def test_preflight_refuses_repository_output(monkeypatch):
    import sys
    monkeypatch.setattr(sys,"platform","linux")
    monkeypatch.setattr(sys,"version_info",(3,12,0))
    with pytest.raises(ValueError,match="outside checkout"):
        preflight(ROOT/"results")
