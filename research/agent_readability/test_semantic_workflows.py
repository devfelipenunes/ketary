import json
import pytest
from semantic_workflows import CASES,VARIANTS,execute,equal,benchmark


@pytest.mark.parametrize("task",CASES,ids=lambda t:t["id"])
@pytest.mark.parametrize("variant",VARIANTS)
def test_workflow(task,variant):
    raw,answer=execute(task,variant)
    _,oracle=execute(task,"qiskit")
    assert equal(answer,oracle)
    json.dumps(raw,allow_nan=False)
    kind=task["kind"]
    if kind=="inspect":
        expected=task["gates"][task["start"]:task["start"]+task["limit"]]
        assert [o["gate"] for o in answer["operations"]]==[g[0] for g in expected]
        assert [o["index"] for o in answer["operations"]]==list(range(task["start"]+1,task["start"]+1+len(expected)))
    elif kind=="evidence":
        assert answer["basis"][task["bits"][0]]["probability"]==pytest.approx(.5)
        assert answer["basis"][task["bits"][1]]["probability"]==pytest.approx(.5)
        assert answer["basis"][task["bits"][2]]["probability"]==pytest.approx(0)
        assert answer["expectations"][task["paulis"][1]]==pytest.approx(1)
        assert answer["norm"]==pytest.approx(1)
        i=int(task["id"][1:])-1
        assert answer["expectations"][task["paulis"][0]]==pytest.approx(0 if i>=4 else (-1 if i%2 else 1))
    elif kind=="verify":
        assert answer["status"]==("PASS" if task["id"] in ("V01","V03") else "FAIL")
        assert answer["checks"]["normalized"]=="PASS"
    else:
        expected={"D01":("FAIL",2,"cx"),"D02":("FAIL",3,"z"),"D03":("PASS",None,None),
                  "D04":("UNSUPPORTED",None,None),"D05":("PASS",None,None),"D06":("FAIL",3,"z")}
        assert (answer["status"],answer["step_index"],answer["actual_operation"])==expected[task["id"]]


def test_benchmark_report():
    result=benchmark()
    assert result["cases"]==24
    assert result["paired_runs"]==72
    assert all(row["semantic_match"] for row in result["rows"])
    assert all(row["raw_json_bytes"]>0 for row in result["rows"])
    assert result==benchmark()
