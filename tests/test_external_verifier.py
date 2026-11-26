import sys
from types import SimpleNamespace
import pytest
import ketary as q

@pytest.mark.parametrize("raw,status",[("equivalent","PASS"),("equivalent_up_to_global_phase","PASS"),("not_equivalent","FAIL"),("probably_equivalent","INCONCLUSIVE"),("equivalent_up_to_phase","INCONCLUSIVE"),("no_information","INCONCLUSIVE")])
def test_external_status_mapping(monkeypatch,raw,status):
    fake=SimpleNamespace(verify_with_hard_timeout=lambda *a,**k:{"equivalence":raw})
    monkeypatch.setitem(sys.modules,"mqt",SimpleNamespace(qcec=fake))
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata,"version",lambda name:"fixture")
    assert q.bell().test.external_equivalence(q.bell())["status"]==status

def test_external_missing_timeout(monkeypatch):
    monkeypatch.setitem(sys.modules,"mqt",None)
    assert q.bell().test.external_equivalence(q.bell())["status"]=="UNSUPPORTED"
    def timeout(*a,**kw):
        raise TimeoutError
    monkeypatch.setitem(sys.modules,"mqt",SimpleNamespace(qcec=SimpleNamespace(verify_with_hard_timeout=timeout)))
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata,"version",lambda name:"fixture")
    assert q.bell().test.external_equivalence(q.bell())["status"]=="INCONCLUSIVE"
