"""B3 follow-up: close known coverage gaps without numerical promotion."""
import json,time
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli as QPauli
from qiskit_aer import AerSimulator
from qcontract import Pauli,StateEigen,prepare
def main():
    rows=[];checks=0
    for n in (8,16,32,64):
        for tc in (16,32):
            for family in ("ghz-phase","local-graph"):
                c=QuantumCircuit(n)
                if family=="ghz-phase":
                    c.h(0)
                    for j in range(1,n):c.cx(j-1,j)
                else:
                    for j in range(n):c.h(j)
                    for j in range(n-1):c.h(j+1);c.cx(j,j+1);c.h(j+1)
                for j in range(tc):
                    wire=j%n;c.t(wire)
                    if family=="local-graph":c.h(wire)
                labels=("I"*(n-1)+"Z","X"*n,"Z"*n,"I"*n)
                specs=tuple(StateEigen(Pauli(x)) for x in labels)
                saved=c.copy()
                for i,x in enumerate(labels):saved.save_expectation_value(QPauli(x),list(range(n)),label=f"obs{i}")
                sim=AerSimulator(method="matrix_product_state",matrix_product_state_truncation_threshold=0.0,max_parallel_threads=1)
                result=sim.run(saved,shots=1).result();assert result.success
                values=tuple(float(complex(result.data(0)[f"obs{i}"]).real) for i in range(4))
                variants={}
                for mode in ("default","plain","phase-weighted"):
                    start=time.perf_counter_ns();p=prepare(c,prepare_state=mode!="default",state_backend=mode if mode!="default" else "plain")
                    prep=(time.perf_counter_ns()-start)/1e6
                    start=time.perf_counter_ns();out=p.verify(*specs);elapsed=(time.perf_counter_ns()-start)/1e6
                    replay=[]
                    for spec,r,v in zip(specs,out,values):
                        if r.status in ("PASS","FAIL"):
                            (a,b),k=r.expectation
                            assert abs((a+b*2**.5)/2**k-v)<1e-8
                            replay.append(p.replay(spec,r))
                            assert replay[-1] is not False
                            checks+=1
                        else:replay.append(None)
                    variants[mode]={"statuses":[r.status for r in out],"routes":[r.route for r in out],"replay":replay,"setup_ms":prep,"query_ms":elapsed}
                rows.append({"width":n,"t_count":tc,"family":family,"variants":variants})
    print(json.dumps({"checks":checks,"rows":rows,"scope":"known B3 high T-count coverage gaps; compare alternative exact state preparations and replay; MPS numerical cross-check only; single exploratory timing"},indent=2))
if __name__=="__main__":main()
