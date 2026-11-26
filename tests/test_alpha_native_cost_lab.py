import itertools
from research.alpha_native_cost_audit import inventory,run
from research.alpha_commutation_lab import direct,packed,masks,run as grouping

def test_all_modules_have_cost_site_inventory():
    audit=inventory()
    assert len(audit["modules"])==26
    assert not audit["eager_cycles"]
    assert all(r["cost_sites"] for r in audit["modules"])

def test_native_access_profile():
    assert len(run(1101,1,quick=True))==2

def test_commutation_predicates_exhaustive():
    labels=["".join(p) for p in itertools.product("IXYZ",repeat=3)]
    for p,q in itertools.product(labels,repeat=2):
        for qwc in (False,True):
            assert packed(masks(p),masks(q),qwc)==direct(p,q,qwc)
    assert direct("XX","ZZ",False) and not direct("XX","ZZ",True)
    assert len(grouping(1101,1,quick=True))==2
