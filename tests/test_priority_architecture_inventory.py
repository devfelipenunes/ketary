"""Selected architecture inventory is executable and source-grounded."""
from research.priority_architecture_audit import inventory

def test_selected_architecture_inventory():
    report=inventory()
    modules=report["modules"]
    assert set(modules)=={"_circuit","_ergonomics","_algorithms","_transpilation","_validation","_adapter","_observable","_result"}
    assert modules["_validation"]["relative_imports"]==[]
    for module in modules.values():
        assert module["lines"]>0 and module["functions"]>0
        assert all(1<=row["line"]<=module["lines"] for row in module["numeric_validation_sites"])
    for name in ("_real","_angle"):
        assert name in {row["function"] for row in modules["_validation"]["numeric_validation_sites"]}
    assert all(len(group)>1 for group in report["identical_bodies"])
