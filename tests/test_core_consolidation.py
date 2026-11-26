"""Guard canonical syntax, legacy schemas and complete classified surface."""
import ast
import json
from pathlib import Path
import pytest
import ketary as q

ROOT=Path(__file__).resolve().parents[1]

def test_inventory_covers_public_declarations_once():
    stub=ast.parse(Path(q.__file__).with_name("__init__.pyi").read_text())
    expected=set(q.__all__)
    for node in stub.body:
        if isinstance(node,ast.ClassDef):
            for member in node.body:
                if isinstance(member,ast.FunctionDef) and not member.name.startswith("_"):
                    expected.add(f"{node.name}.{member.name}")
                elif isinstance(member,ast.AnnAssign) and isinstance(member.target,ast.Name) and not member.target.id.startswith("_"):
                    expected.add(f"{node.name}.{member.target.id}")
    categories=json.loads((ROOT/"docs/api-surface.json").read_text())
    assert set(categories)=={"Core","Advanced","Native","Compatibility"}
    items=[item for group in categories.values() for item in group]
    assert len(items)==len(set(items))
    assert set(items)==expected
    assert {"Circuit.run","Observable","Contract","Result","Circuit.h"}<=set(categories["Core"])
    assert {"Circuit.gates","Circuit.analyze","Circuit.h_many"}<=set(categories["Compatibility"])

def test_observable_aggregate_reuses_snapshot(monkeypatch):
    c=q.bell()
    good,bad=c.run(),c.copy().z(0).run()
    xx=q.X(0)@q.X(1)
    H=2*q.I()+xx
    targets={H:3,"ZZ":1}
    contract=c.contract(expectations=targets)
    targets[H]=1
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("hidden execution"))
    contract.verify(good).require()
    assert contract.verify(bad).status=="FAIL"
    good.test.expectations({xx:1,H:3}).require()
    good.verify(expectations={H:3,"ZZ":1}).require()
    data=contract.to_dict()
    assert data["expectations"]=={"ZZ":1}
    assert data["observable_expectations"]==[{"terms":{"II":2.,"XX":1.},"expected":3.}]
    assert json.loads(contract.verify(good).to_json())==contract.verify(good).to_dict()
    assert json.loads(good.verify(expectations={H:3}).to_json())["status"]=="PASS"
    assert json.loads(good.test.expectation(H,3).to_json())["actual"]==pytest.approx(3)
    assert "FAIL" in contract.verify(bad).render()

def test_legacy_contract_export_and_report_keys():
    c=q.bell()
    contract=c.contract(expectations={"XX":1})
    assert contract.to_dict()=={"num_qubits":2,"probabilities":{},"expectations":{"XX":1},"normalized":False,"atol":1e-9}
    r=c.run()
    assert set(contract.verify(r).to_dict()["checks"])=={"expectation:XX"}
    assert r.verify().status=="UNSUPPORTED"
    with pytest.raises(ValueError):
        c.contract()
    with pytest.raises(TypeError):
        bool(r.test.expectation("XX",1))
    assert r.test.expectation("XX",1).render().startswith("PASS:")

@pytest.mark.parametrize("targets",[{q.Z(3):0},{q.X(0):True},{q.X(0):float("nan")},{"XX":2},{q.X(0):0,q.Observable({"IX":1}):0}])
def test_invalid_aggregate_predicates(targets):
    c=q.bell()
    r=c.run()
    for fn in (lambda:c.contract(expectations=targets),lambda:r.verify(expectations=targets),lambda:r.test.expectations(targets)):
        with pytest.raises(ValueError):
            fn()

def test_observable_checkpoint_contract():
    c=q.bell().checkpoint("good").z(0).checkpoint("bad")
    contract=c.contract(expectations={q.X(0)@q.X(1):1})
    report=c.debug.verify_checkpoints({"good":contract,"bad":contract})
    assert report.status=="FAIL" and report["first_nonpass"]==3

def test_canonical_docs_snippets():
    # Execute the user-facing entry snippets in order using shared locals.
    for name in ("README.md","docs/getting-started.md","docs/core-api.md"):
        ns={}
        text=(ROOT/name).read_text()
        for block in text.split("```python\n")[1:]:
            code=block.split("```",1)[0]
            exec(compile(code,name,"exec"),ns)
