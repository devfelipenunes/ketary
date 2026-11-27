"""F: matched exact Pauli transformation against Stim and Qiskit PauliList."""
import stim
from common5 import *
from qiskit.quantum_info import Clifford,PauliList
from test_engine import native
from benchmark_engine import setup

def stim_circuit(pre):
    c=stim.Circuit()
    c.append("I",[pre.width-1])
    names=("H","S","S_DAG","X","Z","CX")
    for op,a,b in pre.gates:c.append(names[op],[a,b] if op==5 else [a])
    return c

def stim_bits(p):
    x=z=0
    for i in range(len(p)):
        k=p[i]
        if k in (1,2):x|=1<<i
        if k in (2,3):z|=1<<i
    assert p.sign in (1,-1)
    return x,z,int(p.sign==-1)

def main():
    backend=native();rows=[];checks=0
    for n in (16,32):
        for g in (100,10000):
            c,p,obs=setup(n,g,64)
            sc=stim_circuit(p);tab=stim.Tableau.from_circuit(sc);cl=Clifford(c.to_qiskit())
            for m in (1,8,64):
                ps=[o.post for o in obs[:m]]
                qs=PauliList([label(n,v) for v in ps])
                ss=[stim.PauliString(("-" if v[2] else "+")+label(n,(v[0],v[1],0))[::-1]) for v in ps]
                def native_pre():return backend.run(p,ps,"batch" if m>=8 else "scalar")
                def qs_pre():return [bits(x) for x in qs.evolve(cl,frame="h")]
                def stim_pre():return [stim_bits(x.before(tab)) for x in ss]
                def native_full():
                    pp=prepare(c);return backend.run(pp,ps,"batch" if m>=8 else "scalar")
                def qs_full():return [bits(x) for x in qs.evolve(Clifford(c.to_qiskit()),frame="h")]
                def stim_full():
                    pp=prepare(c);tt=stim.Tableau.from_circuit(stim_circuit(pp))
                    return [stim_bits(x.before(tt)) for x in ss]
                fs={"native_prepared":native_pre,"qiskit_list_prepared":qs_pre,"stim_tableau_prepared":stim_pre,
                    "native_full":native_full,"qiskit_list_full":qs_full,"stim_full":stim_full}
                expected=qs_pre()
                for fn in fs.values():assert fn()==expected
                checks+=m*5
                rows.append({"n":n,"gates":g,"m":m,"timings":measure(fs)})
    output({"scope":"signed Pauli transformations only, no contract report; same post Paulis prepared; full includes circuit conversion, output conversion; Stim 1.15 pinned only for CI research","stim":stim.__version__,"checks":checks,"rows":rows})
if __name__=="__main__":main()
