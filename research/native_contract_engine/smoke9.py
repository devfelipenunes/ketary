"""Test installed wheel without SDK dependencies, from outside source tree."""
import ketary_native_research as r
assert r.SCHEMA_VERSION==1
p=r.PackedCircuit(1,bytes((0,0,0)))
assert p.width==1 and p.gate_count==1
assert p.propagate((1,0,0),4096,100)==([(0,1,1,0)],0,1,1)
assert p.transition((0,1,0),(1,0,0),4096,100)==(True,None,1,1)
ok,w,peak,work=p.transition((1,0,0),(1,0,0),4096,100)
assert not ok and w is not None and w[2]!=(0,0)
for n,b in ((True,b""),(0,b""),(65,b""),(2,b"x"),(2,b"\x08\x00\x00"),(2,b"\x05\x00\x00")):
    try:r.PackedCircuit(n,b)
    except (ValueError,OverflowError,TypeError):pass
    else:raise AssertionError("invalid snapshot")
try:r.PackedCircuit(16,bytes(v for i in range(13) for v in (6,i,0))).propagate((65535,0,0),4096,2000000)
except r.BudgetExceeded:pass
else:raise AssertionError("cap")
print("installed extension smoke PASS",r.__file__)
