"""Dependency inventory follows extras even when a root is revisited."""
from types import SimpleNamespace
from tools import audit_dependencies as audit

def test_extra_closure_and_cycles(monkeypatch):
    graph={
        "root": ["child[fast]", "platform-only; sys_platform == 'not-a-platform'"],
        "child": ["plain", "accelerator[simd]; extra == 'fast'", "unused; extra == 'unused'"],
        "accelerator": ["leaf; extra == 'simd'", "child[debug]"],
        "leaf": [], "plain": [], "diagnostic": [],
    }
    graph["child"].append("diagnostic; extra == 'debug'")
    def distribution(name):
        return SimpleNamespace(metadata={"Name":name},version="1.0",
                               requires=graph[name],files=[])
    class Meta(dict):
        def get_all(self,k,default=None):return default
    def dist(name):
        d=distribution(name);d.metadata=Meta(d.metadata);return d
    monkeypatch.setattr(audit.metadata,"distribution",dist)
    out=audit.inventory(("root","child"))
    rows={d["name"]:d for d in out["dependencies"]}
    assert set(rows)=={"root","child","plain","accelerator","leaf","diagnostic"}
    assert rows["child"]["active_extras"]==["debug","fast"]
    assert rows["accelerator"]["active_extras"]==["simd"]
    assert len(rows["child"]["requires"])==3
    assert not rows["root"]["active_extras"]

def test_runtime_roots_unchanged():
    out=audit.inventory(("qiskit","numpy"))
    rows={r["name"].lower().replace("_","-"):r for r in out["dependencies"]}
    assert {"qiskit","numpy","rustworkx","scipy"}<=set(rows)
    assert not {"pytest","mypy","qiskit-aer","mqt-qcec"}&set(rows)
