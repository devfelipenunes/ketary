"""Execute actual compiled contracts. JSON is machine-readable evidence, not simulated UI."""
import argparse,sys,platform,time,statistics,json
from dataclasses import asdict
from importlib.metadata import version
from common5 import *
from native9 import RustSession
from contract_forms11 import Transition,Product,On,requires,CleanAncillas,LabSession
from front_proof10 import build_workspace
from qiskit.quantum_info import Clifford,Pauli,Operator
from test_engine import witness_state
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repetitions",type=int,default=30);ap.add_argument("--json",action="store_true");args=ap.parse_args()
    if not 3<=args.repetitions<=100:raise ValueError("repetitions 3..100")
    checks=0;reject=0;examples=[];rows=[]
    # Same specification across mask, label, explicit wire and fluent forms.
    for n in (2,3,4,5,16,32,64):
        for bad in (False,True):
            c=circuit(n,[(0,0,0)]+[(5,0,i) for i in range(1,n)]+([(4,0,0)] if bad else []))
            s=LabSession.prepare(c)
            pre=Product((On(0,"Z"),));post=Product(tuple(On(i,"X") for i in range(n)))
            forms={"masks":Transition((0,1,0),((1<<n)-1,0,0)),"labels":Transition("I"*(n-1)+"Z","X"*n),"wires":Transition(pre,post),"fluent":requires(pre).ensures(post)}
            reports={k:s.verify(v) for k,v in forms.items()}
            expected=reports["masks"]
            assert all(r==expected for r in reports.values()) and expected.status==("FAIL" if bad else "PASS")
            checks+=len(forms)
            if n<=5:
                u=Operator(c.to_qiskit()).data
                d=u.conj().T@Pauli("X"*n).to_matrix()@u-Pauli("I"*(n-1)+"Z").to_matrix()
                assert (np.max(np.abs(d))<1e-10)==(expected.status=="PASS")
                if expected.witness:
                    w=expected.witness;v=witness_state(w);a,b=w.numerator
                    assert abs(np.vdot(v,d@v).real-(a+b*np.sqrt(2))/(1<<w.denominator_power))<1e-10
            if n==4:examples.append({"name":"GHZ transition mutant" if bad else "GHZ transition","qubits":n,"gates":len(s.engine.packed)//3,"report":asdict(expected)})
            if not bad:
                rows.append({"workload":"GHZ","n":n,"gates":len(s.engine.packed)//3,"timings":measure({k:lambda f=v:s.verify(f) for k,v in forms.items()},reps=args.repetitions)})
    s=LabSession.prepare(circuit(2,[(0,0,0)]))
    for p in ("Z","AIZ","iX",Product((On(0,"X"),On(0,"Z"))),Product((On(True,"X"),)),Product((On(2,"Z"),)),(True,0,0)):
        try:s.verify(Transition(p,"II"))
        except (TypeError,ValueError):reject+=1
        else:raise AssertionError("invalid form")
    for bad in ("none","uncompute"):
        c=build_workspace(4,bad);s=LabSession.prepare(c);r=s.verify(CleanAncillas((2,)))
        assert r.status==("PASS" if bad=="none" else "FAIL")
        examples.append({"name":"Toffoli workspace "+bad,"qubits":4,"gates":len(s.engine.packed)//3,"report":asdict(r)})
    for t in (4,8,12):
        n=64;c=circuit(n,[(4,i%n,0) for i in range(100)]+[(6,i,0) for i in range(t)])
        p=prepare(c,allow_t=True);s=LabSession.prepare(c);contract=Transition("X"*n,"X"*n);obs=(contract.obligation(n),)
        r=s.verify(contract);old=verify(p,obs,method="sparse")[0]
        assert (r.status,r.scope,r.witness)==(old.status,old.scope,old.witness)
        fs={"python_cold":lambda:verify(prepare(c,allow_t=True),obs,method="sparse"),"rust_cold":lambda:contract.verify(c),"rust_warm":lambda:s.verify(contract)}
        rows.append({"workload":"Clifford+T branching","n":n,"gates":len(s.engine.packed)//3,"T":t,"status":r.status,"timings":measure(fs,reps=args.repetitions)})
    report={"scope":"research only; matched transition reports, no public API, shared CI unless run on controlled host","python":platform.python_version(),"platform":platform.platform(),"extension":version("ketary-native-research"),"repetitions":args.repetitions,"form_checks":checks,"invalid_forms":reject,"examples":examples,"rows":rows}
    if args.json:output(report)
    else:
        print("KETARY CONTRACT LAB | "+report["platform"])
        for ex in examples:
            rr=ex["report"];print(ex["name"],rr["status"],rr["reason"],"witness:",rr.get("witness"))
        for row in rows:
            print(row["workload"],row["n"],row.get("T",""),"gates",row["gates"])
            for method,v in row["timings"].items():print(f"  {method:20} p50={v['median_ms']:.6f} ms p95={v['p95_ms']:.6f} ms")
        print("Form checks:",checks,"invalid rejected:",reject)
if __name__=="__main__":main()
