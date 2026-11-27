"""Research-only adaptive planner for exact Pauli obligations."""
from dataclasses import asdict
from common5 import *
from engine import Report,SCOPE,valid_pauli,difference,product_witness
from fast_sparse7 import propagate_fast
from sparse import BudgetExceeded
from front_c6 import reduce_gates
from front_c7 import factor
from front_b import Session
from front_b7 import grouped
from test_engine import native
from benchmark_engine import setup

def cone(gs,post):
    # Backward conservative support union. A gate disjoint from current
    # support commutes with every term; retain original chronological order.
    mask=post[0]|post[1];kept=[]
    for op,a,b in reversed(gs):
        wires=(1<<a)|((1<<b) if op==5 else 0)
        if mask&wires:kept.append((op,a,b));mask|=wires
    return tuple(reversed(kept))
def plan(p,ob,*,budget=2_000_000):
    cid=admission(p);valid_pauli(ob.pre,p.width);valid_pauli(ob.post,p.width)
    if type(budget) is not int or not 1<=budget<=2_000_000:raise ValueError("budget")
    def report(status,method,reason,w=None):return Report(status,method,cid,digest(asdict(ob)),SCOPE,reason,w)
    # Charge conservative preprocessing scans before the bounded propagation.
    cost=3*len(p.gates)
    if cost>=budget:return report("INCONCLUSIVE","planner","preprocess budget")
    reduced=cone(reduce_gates(p),ob.post);remaining=budget-cost
    pp=Prepared(p.width,reduced,bytes(v for row in reduced for v in row))
    if sum(op>=6 for op,_,_ in reduced)>12:
        # Reserve separate budgets; factor is exact but may be inconclusive.
        part=remaining//2
        if part:
            r=factor(pp,ob,budget=part)
            remaining-=part
            if r.status in ("PASS","FAIL"):return report(r.status,"factor-cone",r.reason,r.witness)
    try:r=propagate_fast(p.width,reduced,ob.post,max_work=remaining)
    except BudgetExceeded:return report("INCONCLUSIVE","sparse-cone","propagation budget")
    d=difference(r.terms,r.denominator_power,ob.pre)
    return report("FAIL" if d else "PASS","sparse-cone","exact coefficient comparison",product_witness(p.width,d,r.denominator_power) if d else None)

def run_cliff(s,obs,backend):
    # Threshold is a research heuristic, not universally optimal.
    if len(obs)>=8 and len(set(o.post for o in obs))*2<=len(obs):return grouped(s,obs,backend)
    return s.run(obs,native=backend)

def main():
    from qiskit.quantum_info import Operator,Pauli
    from test_engine import witness_state
    rng=random.Random(7);checks=0;rows=[]
    for n in (2,3,4,5):
        for j in range(32):
            gs=gates(n,24,j)+[(6,0,0),(7,0,0),(6,n-1,0)]
            p=prepare(circuit(n,gs),allow_t=True);u=Operator(circuit(n,gs).to_qiskit()).data
            post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            for pre in (post,(0,0,0)):
                ob=Obligation(pre,post);r=plan(p,ob);delta=u.conj().T@Pauli(label(n,post)).to_matrix()@u-Pauli(label(n,pre)).to_matrix()
                assert r.status==("PASS" if np.max(np.abs(delta))<1e-10 else "FAIL")
                if r.status=="FAIL":
                    v=witness_state(r.witness);a,b=r.witness.numerator;gap=(a+b*np.sqrt(2))/(1<<r.witness.denominator_power)
                    assert abs(np.vdot(v,delta@v).real-gap)<1e-10 and abs(gap)>1e-10
                checks+=1
    # Irrelevant T gates outside a small backward cone: no approximation.
    for n in (16,32,64):
        for count in (1000,10000):
            gs=[(6,1+i%(n-1),0) for i in range(count)]+[(0,0,0)]
            p=prepare(circuit(n,gs),allow_t=True);ob=Obligation((0,1,0),(1,0,0))
            assert plan(p,ob).status=="PASS" and verify(p,(ob,))[0].status=="INCONCLUSIVE"
            assert plan(p,ob,budget=1).status=="INCONCLUSIVE"
            rows.append({"n":n,"gates":len(gs),"retained":len(cone(gs,ob.post)),"timings":measure({"direct":lambda:verify(p,(ob,)),"planner":lambda:plan(p,ob)})})
    backend=native();c,p,base=setup(32,10000,64);s=Session(p)
    for obs in (base,base[:1]*64,base[:8]*8):
        assert semantic(run_cliff(s,obs,backend))==semantic(s.run(obs,native=backend))
    output({"scope":"adaptive research planner, exact Pauli scope; preprocessing bounded by conservative scans, witness costs not included; no silent downgrade","dense_checks":checks,"rows":rows,"clifford_report_checks":192})
if __name__=="__main__":main()
