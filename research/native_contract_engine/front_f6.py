"""Research: matched Stim text construction and tableau, Qiskit vectorized."""
import stim
from common5 import *
from front_f import stim_circuit,stim_bits
from benchmark_engine import setup
from qiskit.quantum_info import Clifford,PauliList
from test_engine import native
def text_circuit(p):
    names=("H","S","S_DAG","X","Z","CX")
    lines=[f"I {p.width-1}"]
    lines.extend(f"{names[op]} {a} {b}" if op==5 else f"{names[op]} {a}" for op,a,b in p.gates)
    return stim.Circuit("\n".join(lines))
def main():
    backend=native();rows=[];checks=0
    for n in (16,32):
        for g in (100,10000):
            c,p,obs=setup(n,g,64);assert stim.Tableau.from_circuit(text_circuit(p))==stim.Tableau.from_circuit(stim_circuit(p))
            for m in (1,8,64):
                ps=[o.post for o in obs[:m]];qs=PauliList([label(n,x) for x in ps]);ss=[stim.PauliString(("+" if x[2]==0 else "-")+label(n,(x[0],x[1],0))[::-1]) for x in ps]
                def st(text):
                    pp=prepare(c);t=stim.Tableau.from_circuit(text(pp))
                    return [stim_bits(x.before(t,targets=range(n))) for x in ss]
                routes={"stim_append":lambda:st(stim_circuit),"stim_text":lambda:st(text_circuit),"qiskit_list":lambda:[bits(x) for x in qs.evolve(Clifford(c.to_qiskit()),frame="h")],"native":lambda:backend.run(prepare(c),ps,"batch" if m>=8 else "scalar")}
                expected=routes["qiskit_list"]()
                for f in routes.values():assert f()==expected
                checks+=3*m
                rows.append({"n":n,"gates":g,"m":m,"timings":measure(routes)})
    output({"scope":"equal Pauli transforms, full circuit preparation, input Paulis prepared, no report; optimized Stim text parser","checks":checks,"rows":rows,"stim":stim.__version__})
if __name__=="__main__":main()
