from research.architecture_inventory import inspect
def test_architecture_audit_inventory():
    audit=inspect()
    assert audit["modules"]==26
    assert not audit["eager_cycles"]
    assert audit["internal_edges"]>=audit["eager_edges"]
    assert not any(a in ("_validation","_gate_specs") for a,b in audit["internal_imports"])
    assert {name for name,dependency in audit["external_imports"] if dependency=="qiskit_aer"}=={"_classical"}
    assert {name for name,dependency in audit["external_imports"] if dependency=="mqt"}=={"_external"}
