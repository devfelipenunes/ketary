"""Executable tutorial and new public API qualification, installed wheels only."""
import json,random,time,statistics
from dataclasses import replace
from fractions import Fraction
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford,PauliList
from qcontract import (prepare,Pauli,Contract,StateEigen,Plan,Named,transition,invariant,zero_input,
                       clean_ancillas,pauli_on,Separable,SumTransition,NoiseAfter,ZBranch,Correctable)
def main():
    checks=0
    def check(ok):
        nonlocal checks
        assert ok;checks+=1
    def reject(fn):
        nonlocal checks
        try:fn()
        except (ValueError,TypeError,AssertionError):checks+=1
        else:raise AssertionError("expected rejection")
    h=QuantumCircuit(1);h.h(0)
    check(Plan((transition("H transforms Z to X",before="Z",after="X"),)).verify(prepare(h)).require().passed)
    c=QuantumCircuit(2);c.h(0);c.cx(0,1)
    plan=Plan((transition("Observable transformation",before="IZ",after="XX"),
               zero_input("Bell X correlation",stabilizes="XX"),
               zero_input("Bell Z correlation",stabilizes="ZZ")))
    p=prepare(c);ok=plan.verify(p);check(ok.require().passed);check(len(ok.explain())==3)
    c.z(0);bad=plan.verify(prepare(c));check([r.status for _,r in bad.results]==["FAIL","FAIL","PASS"]);reject(bad.require)
    check(all(r.status=="INCONCLUSIVE" for _,r in plan.verify(p,max_work=1).results))
    reject(lambda:Plan((plan.obligations[0],plan.obligations[0])))
    reject(lambda:Named("unsupported","not a spec"))
    check(pauli_on(3,((0,"X"),(2,"Y")),negative=True)==Pauli("-YIX"))
    for x in (((0,"X"),(0,"Z")),((3,"X"),),((True,"X"),),((0,"Q"),)):
        reject(lambda:pauli_on(3,x))
    identity=prepare(QuantumCircuit(1))
    both=Plan((invariant("All-input identity",observable="X"),zero_input("Zero state X",stabilizes="X"))).verify(identity)
    check([r.status for _,r in both.results]==["PASS","FAIL"])
    q=QuantumCircuit(2);q.cx(0,1);q.cx(0,1);clean=Plan((clean_ancillas("Return workspace",wires=(1,)),))
    check(clean.verify(prepare(q)).passed);q.cx(0,1);check(not clean.verify(prepare(q)).passed)
    # Explicit wire masks are ergonomic aliases, not a new domain.
    # Verify exact object/report equality, including identities and budgets.
    for label in ("I","X","Y","Z","-Y","-Z"):
        mask=Pauli(label)
        for a,b in ((invariant("same",observable=label),invariant("same",observable=mask)),
                    (zero_input("same",stabilizes=label),zero_input("same",stabilizes=mask)),
                    (transition("same",before=label,after=label),transition("same",before=mask,after=label))):
            check(a==b)
            for budget in (1,2_000_000):
                left=Plan((a,)).verify(identity,max_work=budget)
                right=Plan((b,)).verify(identity,max_work=budget)
                check(left==right)
                row=left.explain()[0];result=left.results[0][1]
                check(row["reserved_work"]==result.reserved and row["has_evidence"]==(result.evidence is not None))
    check(transition("wire 0",before=pauli_on(2,((0,"Z"),)),after="IZ").specification==Contract(requires=Pauli("IZ"),ensures=Pauli("IZ")))
    for bad in ((True,0,0),(0,-1,0),(0,0,2),(1<<64,0,0),(0,0),[0,0,0],None):
        reject(lambda:invariant("bad",observable=bad))
        reject(lambda:zero_input("bad",stabilizes=bad))
        reject(lambda:transition("bad",before="I",after=bad))
    reject(lambda:Plan((zero_input("wide",stabilizes=pauli_on(2,((1,"Z"),))),)).verify(identity))
    # Six additional domain examples; no hidden simulation or hardware call.
    ref=prepare(QuantumCircuit(1));check(ref.check(ref.equivalent_to(ref,strict=True)).passed)
    check(ref.check(ref.action_matches(ref,ancillas=(0,))).passed)
    check(p.check(Separable(1)).status=="FAIL")
    half=((1,0),1);check(p.check(ZBranch(0,0,Pauli("IZ"),half,half)).passed)
    one=prepare(h);z=Pauli("Z");x=Pauli("X");i=Pauli("I")
    check(one.check(SumTransition(((z,Fraction(1,3)),),((x,Fraction(1,3)),))).passed)
    check(one.check(NoiseAfter(z,x,((i,3),(z,1)),4,Fraction(1,2))).passed)
    code=prepare(QuantumCircuit(3));check(code.check(Correctable((Pauli("IZZ"),Pauli("ZZI")),tuple(Pauli(s) for s in ("III","IIX","IXI","XII")))).passed)
    # State tableau: exact independent replay, tamper rejection, comparison
    # with A4's fallback path, and per-item budgets including mixed domains.
    rng=random.Random(5101);rows=[]
    for n in (2,4,8,16,32,64):
        circuit=QuantumCircuit(n)
        for j in range(128):
            a,b=rng.sample(range(n),2)
            if j%3==0:circuit.cx(a,b)
            else:getattr(circuit,rng.choice(("h","s","sdg","x","z")))(a)
        engine=prepare(circuit);cl=Clifford(circuit).adjoint()
        ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(64))
        specs=tuple(StateEigen(x) for x in ps)
        def label(p):
            x,z,s=p
            return ("-" if s else "")+"".join("IZXY"[2*((x>>i)&1)+((z>>i)&1)] for i in reversed(range(n)))
        posts=PauliList([label(p) for p in ps]);img=posts.evolve(cl,frame="s")
        want=tuple(((0 if any(x) else 1-2*(int(ph)//2),0),0) for x,ph in zip(img.x,img.phase))
        new=engine.verify(*specs)
        old=engine._engine.verify(specs)
        for spec,r,o,v in zip(specs,new,old,want):
            check(r.route=="tableau-state" and r.expectation==v)
            check(r.status==o.status and r.obligation==o.obligation and r.reserved==o.reserved)
            check(engine.replay(spec,r) is True)
            check(engine.replay(spec,replace(r,expectation=((3,0),0))) is False)
            check(engine.replay(spec,r,max_work=1) is None)
        transitions=tuple(Contract(requires=(0,0,j%2),ensures=(0,0,0)) for j in range(64))
        for count in (1,8,32,64):
            batch=transitions[:count]
            for quota in (0,1,4*n+6,4*n+7,6*n+7,2_000_000//count):
                budget=max(1,quota*count)
                check(engine.statuses(*batch,max_work=budget)==tuple(r.status for r in engine.verify(*batch,max_work=budget)))
            check(engine.statuses(*specs[:count])==tuple(r.status for r in engine.verify(*specs[:count])))
            routes={"statuses":lambda:engine.statuses(*batch),"reports":lambda:engine.verify(*batch),
                    "state_reports":lambda:engine.verify(*specs[:count]),"legacy_state_reports":lambda:engine._engine.verify(specs[:count])}
            samples={k:[] for k in routes}
            for f in routes.values():f()
            for _ in range(9):
                order=list(routes);rng.shuffle(order)
                for k in order:
                    t=time.perf_counter_ns();routes[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
            rows.append({"width":n,"queries":count,"timings":{k:{"median_ms":statistics.median(v),"samples_ms":v} for k,v in samples.items()}})
        check(engine.statuses(transitions[0],specs[0])==tuple(r.status for r in engine.verify(transitions[0],specs[0])))
        # A mixed request and its individual requests must produce the
        # same full public results at exactly the same per-item quota.
        # Include both eligible and insufficient-budget state observables.
        mixed=(transitions[0],StateEigen((0,0,0)),StateEigen(((1<<n)-1,(1<<n)-1,0)),
               SumTransition((((0,0,0),Fraction(1)),),(((0,0,0),Fraction(1)),)))
        for quota in (0,1,2,3,4,2*n+2,2*n+3,6*n+7,10000):
            budget=max(1,quota*len(mixed))
            got=engine.verify(*mixed,max_work=budget)
            if quota:
                check(got==tuple(engine.check(x,max_work=quota) for x in mixed))
            else:check(all(r.status=="INCONCLUSIVE" for r in got))
        reject(lambda:engine.verify(StateEigen((0,0,0)),Contract(requires=(True,0,0),ensures=(0,0,0))))
        reject(lambda:engine.verify(StateEigen((0,0,0)),StateEigen((True,0,0))))
        reject(lambda:engine.statuses(Contract(requires=(True,0,0),ensures=(0,0,0))))
        check(engine.verify(*specs,max_work=1)[0].status=="INCONCLUSIVE")
    print(json.dumps({"checks":checks,"rows":rows,"scope":"installed candidate named API, all ten families, state replay, budget/status parity and paired exploratory timings"},indent=2,allow_nan=False))
if __name__=="__main__":main()
