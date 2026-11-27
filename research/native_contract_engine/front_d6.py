"""Research: disjoint-wire factorization of product-Pauli invariants."""
from common5 import *
from engine import valid_pauli
from qiskit.quantum_info import Operator,Pauli
def factor(p,ob):
    cid=admission(p);valid_pauli(ob.pre,p.width);valid_pauli(ob.post,p.width)
    # Disjoint one-wire blocks commute; preserve each wire's original order.
    if any(g[0]==5 for g in p.gates):return "UNSUPPORTED",()
    if ob.pre[2]!=ob.post[2] or ob.pre!=ob.post:return "UNSUPPORTED",()
    groups=[[] for _ in range(p.width)]
    for op,a,b in p.gates:groups[a].append((op,0,0))
    local=[]
    for i,gs in enumerate(groups):
        a=((ob.pre[0]>>i)&1,(ob.pre[1]>>i)&1,0)
        pp=Prepared(1,tuple(gs),bytes(v for row in gs for v in row))
        local.append(verify(pp,(Obligation(a,a),))[0])
    # All positive local identities sufficient. Local failures may cancel signs.
    return ("PASS" if all(r.status=="PASS" for r in local) else "INCONCLUSIVE"),tuple(local)
def fixture(n):
    return [(6,i,0) for i in range(n)]+[(7,i,0) for i in range(n)]
def main():
    rows=[];checks=0
    for n in (2,3,4,5,12,13,16,32,64):
        p=prepare(circuit(n,fixture(n)),allow_t=True);x=((1<<n)-1,0,0);ob=Obligation(x,x)
        status,local=factor(p,ob);assert status=="PASS";r=verify(p,(ob,))[0]
        assert r.status==("PASS" if n<=12 else "INCONCLUSIVE")
        if n<=5:
            u=Operator(circuit(n,fixture(n)).to_qiskit()).data
            np.testing.assert_allclose(u,np.eye(1<<n),atol=1e-10);checks+=1
        rows.append({"n":n,"direct":r.status,"factorized":status,"local":len(local),"timings":measure({"direct":lambda:verify(p,(ob,)),"factorized":lambda:factor(p,ob)})})
    p=prepare(circuit(2,[(4,0,0),(4,1,0)]));ob=Obligation((3,0,0),(3,0,0))
    assert factor(p,ob)[0]=="INCONCLUSIVE" and verify(p,(ob,))[0].status=="PASS"
    assert factor(prepare(circuit(2,[(5,0,1)])),ob)[0]=="UNSUPPORTED"
    output({"scope":"sufficient exact product-Pauli preservation on disjoint single-wire gates; local failures never imply global failure; not generic decomposition","dense_checks":checks,"rows":rows})
if __name__=="__main__":main()
