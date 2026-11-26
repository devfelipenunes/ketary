"""Validate manifest pointers without claiming source execution or independent authors."""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_application_atlas_inventory():
    data=json.loads((ROOT/"docs/alpha-application-atlas.json").read_text())
    assert data["schema_version"]==1 and data["target"]==100
    rows=data["rows"]
    ids=[r["id"] for r in rows]
    assert len(ids)==len(set(ids)) and 0<len(ids)<=data["target"]
    pointers=[(r["path"],r["symbol"],r.get("selector")) for r in rows]
    assert len(pointers)==len(set(pointers))
    for row in rows:
        assert row["status"]=="inventoried-authored" and row["scope"]
        path=(ROOT/row["path"]).resolve()
        assert path.is_relative_to(ROOT) and path.is_file()
        tree=ast.parse(path.read_text())
        assert any(isinstance(n,ast.FunctionDef) and n.name==row["symbol"] for n in tree.body)
        if "selector" in row:
            assert any(isinstance(n,ast.Constant) and n.value==row["selector"] for n in ast.walk(tree))
