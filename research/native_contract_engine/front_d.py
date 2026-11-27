"""D: composition of many exact Pauli transition obligations."""
from common5 import *
from qiskit.quantum_info import Clifford,Pauli,Operator
from engine import Report,SCOPE
from dataclasses import asdict

def compose_many(parts,paulis,*,budget=2_000_000):
    if type(parts) is not tuple or not 1<=len(parts)<=100 or type(paulis) is not tuple or len(paulis)!=len(parts)+1:raise ValueError("chain")
    if type(budget) is not int or not len(parts)+1<=budget<=2_000_000:raise ValueError("budget")
    for p in parts:
        admission(p)
        if p.width!=parts[0].width:raise ValueError("width")
    if sum(len(p.gates) for p in parts)>100_000:raise ValueError("gates")
    local=tuple(verify(p,(Obligation(a,b),),max_work=budget//(len(parts)+1))[0] for p,a,b in zip(parts,paulis,paulis[1:]))
    joined=Prepared(parts[0].width,tuple(g for p in parts for g in p.gates),b"".join(p.packed for p in parts))
    ob=Obligation(paulis[0],paulis[-1])
    if all(r.status=="PASS" for r in local):
        return local,Report("PASS","composition",admission(joined),digest(asdict(ob)),SCOPE,"exact matching chain")
    return local,verify(joined,(ob,),max_work=budget//(len(parts)+1))[0]

def fixture(n,count):
    gs=[gates(n,8,119+i) for i in range(count)]
    parts=tuple(prepare(circuit(n,g)) for g in gs)
    p=Pauli("Z"*n);chain=[bits(p)]
    for g in reversed(gs):
        p=p.evolve(Clifford(circuit(n,g).to_qiskit()),frame="h");chain.append(bits(p))
    return parts,tuple(reversed(chain)),prepare(circuit(n,[a for g in gs for a in g]))

def main():
    rows=[];checks=0
    for n in (3,16,32):
        for count in (2,10,100):
            parts,chain,joined=fixture(n,count)
            local,r=compose_many(parts,chain);assert all(x.status=="PASS" for x in local) and r.status=="PASS"
            ref=verify(joined,(Obligation(chain[0],chain[-1]),))[0];assert ref.status==r.status and ref.circuit_id==r.circuit_id;checks+=count
            if n==3:
                u=Operator(circuit(n,list(joined.gates)).to_qiskit()).data
                np.testing.assert_allclose(u.conj().T@Pauli(label(n,chain[-1])).to_matrix()@u,Pauli(label(n,chain[0])).to_matrix(),atol=1e-10)
            rows.append({"n":n,"parts":count,"timings":measure({"local_chain":lambda:compose_many(parts,chain),"direct":lambda:verify(joined,(Obligation(chain[0],chain[-1]),))})})
    x=prepare(circuit(2,[(3,0,0)]));z=(0,1,0);local,r=compose_many((x,x),(z,z,z));assert [i.status for i in local]==["FAIL","FAIL"] and r.status=="PASS"
    output({"scope":"matching exact Pauli identities; no inferred global failure; no persistent cache","local_obligations":checks,"direct_controls":len(rows),"cancel_control":1,"rows":rows})
if __name__=="__main__":main()
