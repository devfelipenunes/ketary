"""Matched authored application diagnostics; no independent usability claim."""
import inspect
import json
import time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.quantum_info import Statevector,Operator,SparsePauliOp
from research.circuit_rewrite_ladder import metrics,stats

def vqe_sdk(t):
    return q.Circuit(2).ry(t,0).cx(0,1)

def vqe_native(t):
    c=QuantumCircuit(2);c.ry(t,0);c.cx(0,1)
    return c

def recovery_sdk(t):
    return q.Circuit(3).ry(t,0).cx(0,1).cx(0,2).x(1).cx(0,2).cx(0,1).ccx(1,2,0)

def recovery_native(t):
    c=QuantumCircuit(3);c.ry(t,0);c.cx(0,1);c.cx(0,2);c.x(1);c.cx(0,2);c.cx(0,1);c.ccx(1,2,0)
    return c

def teleport_sdk(t):
    return q.Circuit(3).ry(t,0).h(1).cx(1,2).cx(0,1).h(0).cx(1,2).cz(0,2)

def teleport_native(t):
    c=QuantumCircuit(3);c.ry(t,0);c.h(1);c.cx(1,2);c.cx(0,1);c.h(0);c.cx(1,2);c.cz(0,2)
    return c

def run(reps=5):
    rows=[]
    for name,ks,ns in [("vqe",vqe_sdk,vqe_native),("bit_recovery",recovery_sdk,recovery_native),("coherent_teleport",teleport_sdk,teleport_native)]:
        for t in (.31,.93,-.72):
            row={"family":name,"angle":t,"paths":{}}
            a,b=np.cos(t/2),np.sin(t/2)
            expected={"vqe":np.array([a,0,0,b]),"bit_recovery":np.array([0,0,a,b,0,0,0,0]),"coherent_teleport":np.kron([a,b],np.ones(4)/2)}[name]
            # Separate complete operator comparison from prepared-state oracle.
            np.testing.assert_allclose(Operator(ks(t).to_qiskit()).data,Operator(ns(t)).data,atol=1e-9,rtol=0)
            histories={"sdk":{"build":[],"run":[]},"native":{"build":[],"run":[]}}
            for i in range(reps):
                for mode,fn in ([("sdk",ks),("native",ns)] if i%2==0 else [("native",ns),("sdk",ks)]):
                    start=time.perf_counter_ns();c=fn(t);mid=time.perf_counter_ns()
                    if mode=="sdk":
                        r=c.run();v=r.math.statevector()
                        objective=.7*r.math.expectation("ZZ")+.2*r.math.expectation("XX") if name=="vqe" else None
                        raw=c.to_qiskit()
                    else:
                        r=Statevector.from_instruction(c);v=r.data.copy()
                        objective=float(r.expectation_value(SparsePauliOp.from_list([("ZZ",.7),("XX",.2)])).real) if name=="vqe" else None
                        raw=c
                    end=time.perf_counter_ns()
                    np.testing.assert_allclose(v,expected,atol=1e-9,rtol=0)
                    if name=="vqe":
                        assert abs(objective-(.7+.4*a*b))<1e-9
                    histories[mode]["build"].append((mid-start)/1e6);histories[mode]["run"].append((end-mid)/1e6)
                    if i==0:
                        lowered=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=1101,qubits_initially_zero=False)
                        np.testing.assert_allclose(Operator(lowered).data,Operator(raw).data,atol=1e-9,rtol=0)
                        source=inspect.getsource(fn)
                        row["paths"][mode]={"source":source,"metrics":metrics(source),"logical_gates":len(raw.data),"basis_gates":len(lowered.data),"basis_depth":lowered.depth()}
            for mode in histories:
                row["paths"][mode].update({k:stats(v) for k,v in histories[mode].items()})
            rows.append(row)
    return {"scope":"authored ideal application slices, timing includes SDK export; shared CI diagnostic; no full optimizer, measured teleportation or noisy hardware claim","rows":rows}

if __name__=="__main__":
    print(json.dumps(run(),indent=2))
