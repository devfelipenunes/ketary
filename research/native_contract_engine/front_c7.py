"""Round 7 C: interaction-component factoring of signed Pauli transitions."""
from common5 import *
from engine import valid_pauli,Report,SCOPE,product_witness
from sparse import propagate,BudgetExceeded
from qiskit.quantum_info import Operator,Pauli
from dataclasses import asdict

def factor(p,ob,budget=2_000_000):
    cid=admission(p);valid_pauli(ob.pre,p.width);valid_pauli(ob.post,p.width)
    if type(budget) is not int or not 1<=budget<=2_000_000:raise ValueError("budget")
    parent=list(range(p.width))
    def root(i):
        while parent[i]!=i:i=parent[i]
        return i
    for op,a,b in p.gates:
        if op==5:parent[root(a)]=root(b)
    groups={}
    for i in range(p.width):groups.setdefault(root(i),[]).append(i)
    rows={k:[] for k in groups};maps={k:{i:j for j,i in enumerate(v)} for k,v in groups.items()}
    for op,a,b in p.gates:
        k=root(a);m=maps[k];rows[k].append((op,m[a],m[b] if op==5 else 0))
    def report(status,reason,w=None):return Report(status,"interaction-factor",cid,digest(asdict(ob)),SCOPE,reason,w)
    sign=ob.post[2]^ob.pre[2];remaining=budget
    for k,wires in groups.items():
        def sub(v):return sum(((v>>i)&1)<<j for j,i in enumerate(wires))
        pre=(sub(ob.pre[0]),sub(ob.pre[1]),0);post=(sub(ob.post[0]),sub(ob.post[1]),0)
        if remaining<1:return report("INCONCLUSIVE","aggregate term-work")
        try:r=propagate(len(wires),rows[k],post,max_work=remaining)
        except BudgetExceeded:return report("INCONCLUSIVE","component budget")
        remaining-=r.work
        d=1<<r.denominator_power
        if r.terms==((pre[0],pre[1],d,0),):continue
        if r.terms==((pre[0],pre[1],-d,0),):sign^=1;continue
        return report("INCONCLUSIVE","local non-Pauli image; direct route required")
    if sign:
        # Exact global image is minus the requested signed Pauli.
        diff={(ob.pre[0],ob.pre[1]):(-2*(-1)**ob.pre[2],0)}
        return report("FAIL","opposite exact global sign",product_witness(p.width,diff,0))
    return report("PASS","exact product of disconnected component transitions")

def fixture(blocks):
    pairs=[(5,2*i,2*i+1) for i in range(blocks)]
    return pairs+[(6,2*i,0) for i in range(blocks)]+[(7,2*i,0) for i in range(blocks)]+pairs
def main():
    checks=0;rows=[];rng=random.Random(711)
    for n in (2,3,4,5):
        for j in range(24):
            gs=gates(n,20,j);p=prepare(circuit(n,gs));post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            qc=circuit(n,gs).to_qiskit()
            u=Operator(qc).data
            from qiskit.quantum_info import Clifford
            evolved=Pauli(label(n,post)).evolve(Clifford(qc),frame="h")
            pre=bits(evolved)
            target=u.conj().T@Pauli(label(n,post)).to_matrix()@u
            oracle_error=float(np.max(np.abs(target-evolved.to_matrix())))
            roundtrip_error=float(np.max(np.abs(evolved.to_matrix()-Pauli(label(n,pre)).to_matrix())))
            direct=propagate(n,p.gates,post)
            info={"n":n,"seed":j,"gates":gs,"post":post,"pre":pre,"label":label(n,pre),"qiskit_label":evolved.to_label(),"phase":int(evolved.phase),"oracle_error":oracle_error,"roundtrip_error":roundtrip_error,"direct_terms":direct.terms}
            assert oracle_error<1e-10,info
            assert roundtrip_error<1e-10,info
            assert direct.terms==((pre[0],pre[1],(-1)**pre[2],0),),info
            for flip in (0,1):
                ob=Obligation((pre[0],pre[1],pre[2]^flip),post);r=factor(p,ob)
                assert r.status==("FAIL" if flip else "PASS")
                expected=u.conj().T@Pauli(label(n,post)).to_matrix()-Pauli(label(n,ob.pre)).to_matrix()
                if flip:
                    from test_engine import witness_state
                    v=witness_state(r.witness);a,b=r.witness.numerator
                    assert abs(np.vdot(v,expected@v).real-a)<1e-10 and b==0
                else:assert np.max(np.abs(expected))<1e-10,{**info,"residual":float(np.max(np.abs(expected))),"report":asdict(r)}
                checks+=1
    for blocks in (2,4,8,12,13,16,32):
        n=2*blocks;gs=fixture(blocks);p=prepare(circuit(n,gs),allow_t=True)
        # X on both wires of each pair turns into X on control during conjugation.
        post=((1<<n)-1,0,0);ob=Obligation(post,post)
        direct=verify(p,(ob,))[0];r=factor(p,ob);assert r.status=="PASS"
        assert direct.status==("PASS" if blocks<=12 else "INCONCLUSIVE")
        rows.append({"n":n,"blocks":blocks,"direct":direct.status,"factor":r.status,"timings":measure({"direct_report":lambda:verify(p,(ob,)),"factor_report":lambda:factor(p,ob)})})
    p=prepare(circuit(2,[(4,0,0),(4,1,0)]));x=(3,0,0);assert factor(p,Obligation(x,x)).status=="PASS"
    p=prepare(circuit(2,[(6,0,0)]),allow_t=True);assert factor(p,Obligation(x,x)).status=="INCONCLUSIVE"
    output({"scope":"exact connected-component factorization for Pauli products; entanglement within components allowed; non-Pauli local image inconclusive; no general circuit equivalence","dense_checks":checks,"rows":rows})
if __name__=="__main__":main()
