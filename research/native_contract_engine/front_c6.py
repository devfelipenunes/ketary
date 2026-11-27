"""Research: exact adjacent inverse cancellation before sparse propagation."""
from common5 import *
from sparse import propagate,BudgetExceeded
from engine import difference
from qiskit.quantum_info import Operator,Pauli
INV={0:0,1:2,2:1,3:3,4:4,5:5,6:7,7:6}
def reduce_gates(p):
    admission(p);stack=[]
    for op,a,b in p.gates:
        if stack and stack[-1]==(INV[op],a,b):stack.pop()
        else:stack.append((op,a,b))
    return tuple(stack)
def check(p,ob):
    try:r=propagate(p.width,reduce_gates(p),ob.post)
    except BudgetExceeded:return "INCONCLUSIVE"
    return "FAIL" if difference(r.terms,r.denominator_power,ob.pre) else "PASS"
def main():
    rng=random.Random(42);checks=0;rows=[]
    for n in (2,3,4,5):
        for j in range(24):
            gs=gates(n,20,j)
            for k in range(6):
                i=rng.randrange(len(gs)+1);a=rng.randrange(n);gs[i:i]=[(6,a,0),(7,a,0)]
            p=prepare(circuit(n,gs),allow_t=True);reduced=reduce_gates(p)
            u=Operator(circuit(n,gs).to_qiskit()).data;v=Operator(circuit(n,list(reduced)).to_qiskit()).data
            np.testing.assert_allclose(u,v,atol=1e-10)
            post=(rng.getrandbits(n),rng.getrandbits(n),0);ob=Obligation(post,post)
            assert check(p,ob)==verify(p,(ob,))[0].status;checks+=1
    for n in (16,32,64):
        for pairs in (16,32,128,1000):
            p=prepare(circuit(n,[(6,0,0),(7,0,0)]*pairs),allow_t=True);ob=Obligation((1,0,0),(1,0,0))
            r=check(p,ob);assert r=="PASS";old=verify(p,(ob,))[0].status;assert old==("PASS" if pairs<=16 else "INCONCLUSIVE")
            rows.append({"n":n,"pairs":pairs,"original":old,"reduced":r,"timings":measure({"baseline":lambda:verify(p,(ob,)),"rewrite":lambda:check(p,ob)})})
    output({"scope":"exact inverse rules on admitted gates; rewrite before sparse cap; no general optimizer or new public limit","dense_checks":checks,"rows":rows})
if __name__=="__main__":main()
