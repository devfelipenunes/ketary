"""Guard the reconciliation and preflight; do not infer closure from routing."""
import ast
import json
from pathlib import Path
import pytest
import ketary as q

ROOT=Path(__file__).resolve().parents[1]

def test_reconciliation_exact_historical_scope():
    ledger=json.loads((ROOT/"docs/alpha-final-technical-ledger.json").read_text())
    old=json.loads((ROOT/"docs/backlog-closure-inventory.json").read_text())
    rows=ledger["historical_expressivity"]
    expected={x["issue"]:x["title"] for x in old["lanes"]["expressivity"]}
    assert len(rows)==52
    assert {x["issue"]:x["title"] for x in rows}==expected
    assert len({x["issue"] for x in rows})==52
    for row in rows:
        assert row["disposition"] in {"qualified","consolidated","not-planned","historical-closed","open"}
        assert row["evidence"] and row["source"]
        if not row["source"].startswith("#"):assert (ROOT/row["source"]).is_file()
    assert {x["issue"] for x in rows if x["disposition"]=="open"}=={56,345}
    assert ledger["excluded"]==[35,100,165,462,460]

def test_capped_method_inventory_exact():
    ledger=json.loads((ROOT/"docs/alpha-final-technical-ledger.json").read_text())
    tree=ast.parse((ROOT/"src/ketary/__init__.pyi").read_text())
    explicit=set()
    for cls in tree.body:
        if not isinstance(cls,ast.ClassDef):continue
        for fn in cls.body:
            if not isinstance(fn,ast.FunctionDef):continue
            args=fn.args.posonlyargs+fn.args.args+fn.args.kwonlyargs
            if any(a.arg in {"max_bytes","max_work","max_qubits","max_steps","max_gates","max_outcomes","max_rank","max_rows","max_attempts","max_depth","max_terms","max_iterations"} for a in args):
                explicit.add(cls.name+"."+fn.name)
    rows=ledger["capped_methods"]
    assert len(rows)==len(explicit)==39
    assert {r["method"] for r in rows}==explicit
    for row in rows:
        assert row["contract"] and row["tests"]
        for path in row["implementation"].split(" / "):assert (ROOT/"src/ketary"/path).is_file()
        for path in row["tests"].split("; "):assert (ROOT/"tests"/path).is_file()

@pytest.mark.parametrize("late",["1","0x",None,3])
def test_table_preflights_all_labels(monkeypatch,late):
    r=q.bell().run()
    monkeypatch.setattr(type(r.math),"amplitude",lambda *a,**k:pytest.fail("table queried before label preflight"))
    with pytest.raises(ValueError):r.math.table(["00",late])

def test_table_preserves_order_duplicates_and_empty():
    r=q.bell().run()
    assert [line.split(" | ")[0] for line in r.math.table(["11","00","11"]).splitlines()[1:]]==["11","00","11"]
    assert r.math.table([])=="basis | amplitude | probability"
    assert "omitted" in r.math.table(max_rows=1)
    with pytest.raises(q.ResourceLimit):r.math.table(["11","00"],max_rows=1)
