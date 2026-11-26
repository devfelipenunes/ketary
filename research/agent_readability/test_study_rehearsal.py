import pytest
from corpus_v03 import CASES,FRAMEWORKS
from ketary_eval import reference
from study_rehearsal import assignment,evaluate_run,paired_summary


def test_assignment_balances_framework_order_and_disjoint_families():
    by_id={c["id"]:c for c in CASES}
    first=[]
    for arm in range(6):
        packet=assignment(arm)
        first.append(packet[0]["framework"])
        ids=[task["id"] for group in packet for task in group["tasks"]]
        assert len(ids)==len(set(ids))==180
        families=[{(by_id[t["id"]]["kind"],by_id[t["id"]]["family"]) for t in g["tasks"]} for g in packet]
        assert not families[0]&families[1] and not families[1]&families[2] and not families[0]&families[2]
    assert all(first.count(f)==2 for f in FRAMEWORKS)


def manifest(framework,participant,study="agent",missing=False):
    return {"study":study,"participant":participant,"replicate":0,
            "model_version":"synthetic-fixture" if study=="agent" else None,
            "framework":framework,"condition":"card",
            "responses":[] if missing else [
                {"id":c["id"],"response":reference(c,framework),"elapsed_ms":0,
                 "input_tokens":0 if study=="agent" else None,"output_tokens":0 if study=="agent" else None,
                 "tool_calls":0,"repair_rounds":0} for c in CASES]}


def test_complete_paired_rehearsal():
    runs=[evaluate_run(manifest(f,p,missing=f=="qiskit")) for p in ("fixture-a","fixture-b") for f in FRAMEWORKS]
    report=paired_summary(runs,repeats=100)
    by={x["comparator"]:x for x in report["comparisons"]}
    assert by["qiskit"]["mean_pass_rate_difference"]==1
    assert by["ketary"]["mean_pass_rate_difference"]==0
    assert by["qiskit"]["participant_clusters"]==2
    assert report["corpus"]=="public-v03-calibration"
    with pytest.raises(ValueError):
        paired_summary(runs[:-1],repeats=100)
    with pytest.raises(ValueError):
        paired_summary(runs+[runs[0]],repeats=100)


def test_human_manifest_and_missing():
    data=manifest("candidate","fixture-human",study="human")
    assert evaluate_run(data)["pass"]==180
    data["responses"][0]["input_tokens"]=10
    with pytest.raises(ValueError):
        evaluate_run(data)
    assert evaluate_run(manifest("candidate","fixture",missing=True))["pass"]==0
