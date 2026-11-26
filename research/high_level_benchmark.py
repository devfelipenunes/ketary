"""Matched high-level workload timings; raw shared-run diagnostics only."""
import argparse
import json
import os
import subprocess
import sys
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit.library import n_local
from qiskit.quantum_info import Operator, SparsePauliOp, Statevector
import ketary as q
from longitudinal_benchmark import paired


def native_ansatz(n,reps):
    return n_local(n,rotation_blocks=["ry","rz"],entanglement_blocks="cx",
                   entanglement="circular",reps=reps,parameter_prefix="w")


def sdk_ansatz(n,reps):
    return q.ansatz(n,rotations=("ry","rz"),entanglement="circular",reps=reps,prefix="w")


def equal_ansatz(a,b):
    values=np.linspace(-.3,.8,len(a.parameters))
    assert a.assign_parameters(values)==b.bind(values).to_qiskit()


def run(reps,seed,smoke=False):
    results=[]
    def add(name,params,functions,verify):
        verify(functions["native"](),functions["sdk"]())
        row={"case":name,**params,**paired(functions,reps,seed+len(results))}
        results.append(row)
        print(json.dumps({"case":name,**params,"medians_ms":{
            k:v["median_ms"] for k,v in row["samples"].items()}}),file=sys.stderr,flush=True)
    for n,depth in ([(4,1)] if smoke else [(4,2),(8,4),(32,8)]):
        add("ansatz_construct",{"n":n,"reps":depth},
            {"native":lambda:native_ansatz(n,depth),"sdk":lambda:sdk_ansatz(n,depth)},equal_ansatz)
        native,sdk=native_ansatz(n,depth),sdk_ansatz(n,depth)
        values=np.linspace(-.3,.8,len(native.parameters))
        add("ansatz_bind",{"n":n,"reps":depth,"parameters":len(values)},
            {"native":lambda:native.assign_parameters(values),
             "sdk":lambda:sdk.bind(values).to_qiskit()},
            lambda a,b:equal_circuits(a,b))
    for n in ([4] if smoke else [4,16,32]):
        edges=q.ring(range(n))
        weights=np.linspace(.2,1.3,len(edges))
        def native_h():
            terms=[("I"*n,float(sum(weights)/2))]
            for (a,b),w in zip(edges,weights,strict=True):
                label=["I"]*n
                label[n-1-a]=label[n-1-b]="Z"
                terms.append(("".join(label),float(-w/2)))
            return SparsePauliOp.from_list(terms)
        def sdk_h():
            return q.maxcut_hamiltonian(n,edges,weights=weights).to_qiskit()
        add("hamiltonian",{"n":n,"edges":len(edges)},{"native":native_h,"sdk":sdk_h},equal_paulis)
    for n,marks in ([(3,2)] if smoke else [(3,2),(6,16),(8,64)]):
        labels=[format(i,f"0{n}b") for i in range(marks)]
        def native_oracle():
            c=QuantumCircuit(n)
            for label in labels:
                zero=[i for i,b in enumerate(reversed(label)) if b=="0"]
                if zero: c.x(zero)
                if n==2: c.cz(0,1)
                else:
                    c.h(n-1)
                    c.mcx(list(range(n-1)),n-1)
                    c.h(n-1)
                if zero: c.x(zero)
            return c
        def sdk_oracle():
            return q.phase_oracle(labels).to_qiskit()
        def check_oracle(a,b):
            np.testing.assert_allclose(Operator(a).data,Operator(b).data,atol=1e-10,rtol=0)
        add("phase_oracle",{"n":n,"marks":marks},{"native":native_oracle,"sdk":sdk_oracle},check_oracle)
    for n,count in ([(4,2)] if smoke else [(8,8),(12,16),(16,16)]):
        sdk=q.Circuit(n).h(0).cx(pairs=q.chain(range(n)))
        native=sdk.to_qiskit()
        labels=[format(i,f"0{n}b") for i in range(count)]
        add("multiple_inputs",{"n":n,"inputs":count},
            {"native":lambda:tuple(Statevector.from_label(v).evolve(native).data.copy() for v in labels),
             "sdk":lambda:tuple(r.math.statevector() for r in sdk.run_many(labels))},equal_numeric)
    for n,rows in ([(4,2)] if smoke else [(4,8),(6,32)]):
        sdk=q.ansatz(n,reps=2,prefix="p")
        native=sdk.to_qiskit()
        values=np.linspace(-.3,.8,rows*len(sdk.parameters)).reshape(rows,-1)
        add("sweep_end_to_end",{"n":n,"rows":rows,"parameters":len(sdk.parameters)},
            {"native":lambda:tuple(Statevector.from_instruction(native.assign_parameters(row)).data.copy()
                                   for row in values),
             "sdk":lambda:tuple(r.math.statevector() for r in sdk.sweep_rows(values).run())},equal_numeric)
    for n,count in ([(4,2)] if smoke else [(8,16),(12,64),(17,256)]):
        sdk=q.ghz(n).run()
        native=Statevector(sdk.math.statevector())
        labels=[format(i,f"0{n}b") for i in range(count)]
        add("selected_probabilities",{"n":n,"queries":count},
            {"native":lambda:{label:float(abs(native.data[int(label,2)])**2) for label in labels},
             "sdk":lambda:sdk.math.probabilities(bits=labels)},
            lambda a,b:equal_numeric(list(a.values()),list(b.values())))
    return {"scope":"matched shared-run diagnostic; output ownership and validation costs included",
            "commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "qiskit":qiskit.__version__,"numpy":np.__version__,"seed":seed,"repetitions":reps,
            "cases":results}


def equal_circuits(a,b):
    assert a==b


def equal_paulis(a,b):
    left=dict(a.to_list())
    right=dict(b.to_list())
    assert left.keys()==right.keys()
    np.testing.assert_allclose([left[k] for k in sorted(left)],[right[k] for k in sorted(right)],atol=1e-12,rtol=0)


def equal_numeric(a,b):
    np.testing.assert_allclose(a,b,atol=1e-9,rtol=0)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--smoke",action="store_true")
    a=p.parse_args()
    if not 3<=a.repetitions<=100 or (not a.smoke and a.repetitions<20):
        p.error("20..100 repetitions (smoke 3..100)")
    print(json.dumps(run(a.repetitions,a.seed,a.smoke),indent=2,allow_nan=False))
