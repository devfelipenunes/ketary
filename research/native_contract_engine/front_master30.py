"""R30 integrated exact contract matrix and deterministic hostile-input campaign."""
import json,random,sys
from dataclasses import replace
from native9 import RustSession
from qualified30 import Engine,Policy,Transition,StateEigen,CleanInput,RelativeAction,Equivalent,Separable,ZBranch
from independent20 import verify_transition
from front_master28 import pack
import ketary_native_research as rn

def integrated():
    checks=0;rows=[]
    for n in (2,3,4,5):
        s=RustSession(n,b"");e=Engine.prepare(s,Policy(prepare_state=True,state_fallback=True))
        z=(0,1,0);x=(1,0,0);i=(0,0,0)
        phase=RustSession(n,pack([(4,0,0),(3,0,0),(4,0,0),(3,0,0)]))
        dirty=RustSession(n,pack([(3,n-1,0)]))
        one=((1,0),0);zero=((0,0),0)
        xs=(Transition(z,z),StateEigen(z),CleanInput((n-1,)),RelativeAction(s,(n-1,)),
            Equivalent(phase),Equivalent(phase,True),Separable(1),
            ZBranch(0,0,z,one,one),ZBranch(0,1,z,zero,zero),ZBranch(0,1,z,one,one),
            RelativeAction(dirty,(n-1,)))
        r=e.verify(xs)
        expect=["PASS","PASS","PASS","PASS","PASS","FAIL","PASS","PASS","PASS","FAIL","FAIL"]
        assert [v.status for v in r]==expect
        assert sum(v.reserved for v in r)<=2_000_000
        assert len(set(v.obligation for v in r))==len(r)
        assert r[4].snapshots==r[5].snapshots==(s.identity,phase.identity)
        assert r[4].domain!=r[5].domain
        assert all(v.status=="INCONCLUSIVE" for v in e.verify(xs,max_work=1))
        bell=Engine.prepare(RustSession(n,pack([(0,0,0),(5,0,1)])),Policy(prepare_state=True))
        half=((1,0),1)
        actual=bell.verify((Separable(1),CleanInput((1,)),ZBranch(0,0,z,half,half),ZBranch(0,1,z,half,((-1,0),1))))
        assert [v.status for v in actual]==["FAIL","FAIL","PASS","PASS"]
        checks+=20;rows.append({"n":n,"domains":list(dict.fromkeys(v.domain for v in r)),"verdicts":[v.status for v in r]})
    s=RustSession(64,b"");e=Engine.prepare(s)
    assert [v.status for v in e.verify((Equivalent(s),Equivalent(s,True),Separable(1))) ]==["UNSUPPORTED"]*3
    for invalid in (ZBranch(0,1,(0,0,0),((2,0),1),((0,0),0)),CleanInput((True,)),Equivalent(s,1),Separable(0)):
        try:e.verify((StateEigen((0,0,0)),invalid))
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError("preflight")
    return {"checks":checks+3,"rows":rows,"scope":"typed exact domain adapter; packed phase excludes source global-phase metadata"}

def fuzz():
    rng=random.Random(3001);checks=0;decisive=0;invalid=0
    for n in (2,3,4,5):
        for seed in range(64):
            gs=[]
            for _ in range(rng.randrange(0,25)):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            g=pack(gs);s=RustSession(n,g);post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            p=s.propagate(post);t=p.terms
            pre=(t[0][0],t[0][1],int(t[0][2]<0)) if len(t)==1 and t[0][3]==0 and abs(t[0][2])==1<<p.denominator_power else (rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            for a in (pre,(pre[0],pre[1],pre[2]^1)):
                want=verify_transition(n,g,a,post).status
                r=Engine.prepare(s).verify((Transition(a,post),))[0]
                assert r.status in (want,"INCONCLUSIVE")
                if r.status==want:decisive+=1
                checks+=1
            for bad in (g+bytes((rng.randrange(8,256),0,0)),g+b"x",g+bytes((5,0,0))):
                try:rn.PackedCircuit(n,bad)
                except (ValueError,TypeError,OverflowError):invalid+=1
                else:raise AssertionError("malformed snapshot")
                checks+=1
    return {"checks":checks,"decisive":decisive,"valid_queries":512,"invalid_rejections":invalid,"seed":3001,"scope":"deterministic generated cases, not coverage-guided fuzzer"}

def metered():
    rng=random.Random(3002);checks=0;rows=[]
    for n in (2,4,8,16,32,64):
        gs=[]
        for _ in range(64):
            a,b=rng.sample(range(n),2);op=rng.randrange(6);gs.append((op,a,b if op==5 else 0))
        gs.extend((6,i%n,0) for i in range(4))
        s=RustSession(n,pack(gs))
        for _ in range(32):
            a=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));b=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            old=s.native.transition(a,b,128,2_000_000)
            got=s.native.transition_metered(a,b,128,2_000_000)
            assert got[:3]==old[:3] and got[4]==old[3]
            assert got[3]==2*len(gs)+got[5]+got[4]<=2_000_000
            assert got[6]<=65
            assert s.native.transition_metered(a,b,128,got[3])==got
            try:s.native.transition_metered(a,b,128,got[3]-1)
            except rn.BudgetExceeded:pass
            else:raise AssertionError("one-unit budget boundary")
            checks+=3
        rows.append({"n":n,"gate_count":len(gs),"reserved_diagnostics":got[5],"last_kernel_work":got[4],"last_final_coefficient_bits":got[6]})
    return {"checks":checks,"rows":rows,"scope":"opt-in logical reservation for scan, sort/diagnostic visits and result construction; no allocation or bit-operation guarantee"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"integrated":integrated,"fuzz":fuzz,"metered":metered}[sys.argv[1]]()},indent=2,allow_nan=False))
