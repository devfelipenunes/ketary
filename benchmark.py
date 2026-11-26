"""Preliminary timing only. Run after all required tests pass."""
import json
import platform
import sys
import time
import statistics
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import ketary as q

def make_native(n,gates):
    c=QuantumCircuit(n)
    for i in range(gates): c.h(i%n)
    return c

def make_wrapped(n,gates):
    c=q.Circuit(n)
    for i in range(gates): c.gates.h(i%n)
    return c

def measure(fn,repetitions=30):
    for _ in range(3): fn()
    values=[]
    for _ in range(repetitions):
        start=time.perf_counter_ns()
        fn()
        values.append((time.perf_counter_ns()-start)/1e6)
    return {"median_ms":statistics.median(values),"p95_ms":float(np.percentile(values,95)),"raw_ms":values}

def main():
    results={"python":sys.version,"platform":platform.platform(),"qiskit":qiskit.__version__,"numpy":np.__version__,"cases":[]}
    for n,gates in [(8,1000),(8,10000),(12,100)]:
        raw=make_native(n,gates); wrapped=make_wrapped(n,gates)
        np.testing.assert_allclose(Statevector.from_instruction(raw).data,wrapped.run().math.statevector(),atol=1e-9)
        for case,base,trial in [("build",lambda:make_native(n,gates),lambda:make_wrapped(n,gates)),("statevector",lambda:Statevector.from_instruction(raw).data.copy(),lambda:wrapped.run().math.statevector())]:
            a,b=measure(base),measure(trial)
            results["cases"].append({"case":case,"n":n,"gates":gates,"native":a,"sdk":b,"overhead_percent":100*(b["median_ms"]/a["median_ms"]-1)})
    print(json.dumps(results,indent=2))

if __name__=="__main__": main()
