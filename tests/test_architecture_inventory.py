from research.architecture_inventory import inspect
def test_architecture_audit_inventory():
    audit=inspect()
    assert audit["modules"]==26
    assert not audit["eager_cycles"]
    assert audit["internal_edges"]>=audit["eager_edges"]
    assert not any(a in ("_validation","_gate_specs") for a,b in audit["internal_imports"])
    assert {name for name,dependency in audit["external_imports"] if dependency=="qiskit_aer"}=={"_classical"}
    assert {name for name,dependency in audit["external_imports"] if dependency=="mqt"}=={"_external"}


def test_every_runtime_module_has_exactly_one_primary_owner():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    registry=json.loads((root/"docs/module-ownership.json").read_text())
    names=[n for group in registry["groups"].values() for n in group]
    assert len(names)==len(set(names))
    assert set(names)==set(inspect()["module_stats"])
    assert "_topology" in registry["groups"]["construction"]
