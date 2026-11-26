"""Guard initial mathematical-contract references; not a semantic proof."""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_mathematical_contract_matrix_references():
    data=json.loads((ROOT/"docs/mathematical-contract-matrix.json").read_text())
    public={n for group in json.loads((ROOT/"docs/api-surface.json").read_text()).values() for n in group}
    assert data["schema_version"]==1
    ids=set(); entries=set()
    for row in data["families"]:
        assert row["id"] not in ids and row["contract"]
        ids.add(row["id"])
        assert row["status"]=="linked_review_required"
        assert row["entries"] and len(row["entries"])==len(set(row["entries"]))
        assert set(row["entries"])<=public and not entries.intersection(row["entries"])
        entries.update(row["entries"])
        assert row["positive"]!=row["negative"]
        for field in ("positive","negative"):
            path,node=row[field].split("::")
            assert path.startswith(("tests/","research/probes/"))
            p=(ROOT/path).resolve()
            assert p.is_relative_to(ROOT) and p.is_file()
            tree=ast.parse(p.read_text(encoding="utf-8"))
            assert node.startswith("test_")
            assert any(isinstance(n,ast.FunctionDef) and n.name==node for n in tree.body)
