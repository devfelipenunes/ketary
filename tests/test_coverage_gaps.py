"""Coverage-gap reporting tests; no artificial coverage thresholds."""
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location("coverage_gaps",Path(__file__).resolve().parents[1]/"research"/"coverage_gaps.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def entry(lines,branches,percent):
    return {"summary":{"num_statements":20,"num_branches":8,"percent_covered":percent},
            "missing_lines":lines,"missing_branches":branches}
def test_normalization_and_count_delta():
    a=module.gaps({"files":{"src/ketary/_result.py":entry([1,2],[[1,2]],80),"tests/x.py":entry([],[],100)}})
    b=module.gaps({"files":{"src/ketary/_result.py":entry([4],[],90),"src/ketary/_plan.py":entry([],[],100)}})
    assert list(a)==["_result.py"]
    assert module.compare(b,a)==[
        {"module":"_plan.py","status":"added","missing_line_delta":None,"missing_branch_delta":None,"coverage_percent_delta":None},
        {"module":"_result.py","status":"matched","missing_line_delta":-1,"missing_branch_delta":-1,"coverage_percent_delta":10}]
def test_empty_and_duplicate_sources_rejected():
    with pytest.raises(ValueError):module.gaps({"files":{}})
    with pytest.raises(ValueError):module.gaps({"files":{"src/ketary/a.py":entry([],[],100),"/tmp/src/ketary/a.py":entry([],[],100)}})
