"""COMP01 B/C: matched authored solutions, not independent usability trials."""
import argparse
import ast
import inspect
import io
import json
import random
import statistics
import subprocess
import time
import tokenize

import cirq
import ketary as q
import numpy as np
import pennylane as qml
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate
from qiskit.quantum_info import SparsePauliOp, Statevector


def ketary_ghz(n):
    return q.ghz(n).run().math.statevector()


def qiskit_ghz(n):
    c = QuantumCircuit(n)
    c.h(0)
    for w in range(n-1):
        c.cx(w,w+1)
    return Statevector.from_instruction(c).data.copy()


def cirq_ghz(n):
    w = cirq.LineQubit.range(n)
    c = cirq.Circuit(cirq.H(w[0]),(cirq.CNOT(w[i],w[i+1]) for i in range(n-1)))
    return cirq.Simulator(dtype=np.complex128).simulate(c,qubit_order=w[::-1]).final_state_vector.copy()


def pennylane_ghz(n):
    dev = qml.device("default.qubit",wires=list(reversed(range(n))))
    @qml.qnode(dev,interface=None,diff_method=None)
    def program():
        qml.Hadamard(0)
        for w in range(n-1):
            qml.CNOT(wires=[w,w+1])
        return qml.state()
    return np.asarray(program()).copy()


def ketary_qft(n):
    return q.Circuit(n).x(0).apply(q.qft(n)).run().math.statevector()


def qiskit_qft(n):
    c = QuantumCircuit(n)
    c.x(0)
    c.append(QFTGate(n),range(n))
    return Statevector.from_instruction(c).data.copy()


def cirq_qft(n):
    w = cirq.LineQubit.range(n)
    c = cirq.Circuit(cirq.X(w[0]),cirq.qft(*w[::-1]))
    return cirq.Simulator(dtype=np.complex128).simulate(c,qubit_order=w[::-1]).final_state_vector.copy()


def pennylane_qft(n):
    dev = qml.device("default.qubit",wires=list(reversed(range(n))))
    @qml.qnode(dev,interface=None,diff_method=None)
    def program():
        qml.PauliX(0)
        qml.QFT(wires=list(reversed(range(n))))
        return qml.state()
    return np.asarray(program()).copy()


def ketary_bv(mask):
    return q.bernstein_vazirani(mask).run().math.statevector()


def qiskit_bv(mask):
    n = len(mask)
    c = QuantumCircuit(n+1)
    c.x(n)
    c.h(range(n+1))
    for i,bit in enumerate(reversed(mask)):
        if bit=="1":
            c.cx(i,n)
    c.h(range(n))
    return Statevector.from_instruction(c).data.copy()


def cirq_bv(mask):
    n = len(mask)
    w = cirq.LineQubit.range(n+1)
    c = cirq.Circuit(cirq.X(w[n]),cirq.H.on_each(*w))
    c.append(cirq.CNOT(w[i],w[n]) for i,bit in enumerate(reversed(mask)) if bit=="1")
    c.append(cirq.H.on_each(*w[:n]))
    return cirq.Simulator(dtype=np.complex128).simulate(c,qubit_order=w[::-1]).final_state_vector.copy()


def pennylane_bv(mask):
    n = len(mask)
    dev = qml.device("default.qubit",wires=list(reversed(range(n+1))))
    @qml.qnode(dev,interface=None,diff_method=None)
    def program():
        qml.PauliX(n)
        for w in range(n+1):
            qml.Hadamard(w)
        for i,bit in enumerate(reversed(mask)):
            if bit=="1":
                qml.CNOT(wires=[i,n])
        for w in range(n):
            qml.Hadamard(w)
        return qml.state()
    return np.asarray(program()).copy()


def ketary_gradient(theta):
    p = q.Circuit.parameter("theta")
    c = q.Circuit.symbolic(2).ry(p,0).cx(0,1)
    h = .5*(q.Z(0)+q.Z(1))+.7*(q.X(0)@q.X(1))
    energy = c.bind({p:theta}).run().math.expectation(h)
    gradient = c.expectation_jacobian({p:theta},[h])[0][0]
    return np.array([energy,gradient])


def qiskit_gradient(theta):
    h = SparsePauliOp.from_list([("IZ",.5),("ZI",.5),("XX",.7)])
    def energy(t):
        c = QuantumCircuit(2)
        c.ry(t,0)
        c.cx(0,1)
        return Statevector.from_instruction(c).expectation_value(h).real
    return np.array([energy(theta),.5*(energy(theta+np.pi/2)-energy(theta-np.pi/2))])


def cirq_gradient(theta):
    a,b = cirq.LineQubit.range(2)
    h = .5*cirq.Z(a)+.5*cirq.Z(b)+.7*cirq.X(a)*cirq.X(b)
    sim = cirq.Simulator(dtype=np.complex128)
    def energy(t):
        c = cirq.Circuit(cirq.ry(t)(a),cirq.CNOT(a,b))
        return sim.simulate_expectation_values(c,observables=[h])[0].real
    return np.array([energy(theta),.5*(energy(theta+np.pi/2)-energy(theta-np.pi/2))])


def pennylane_gradient(theta):
    dev = qml.device("default.qubit",wires=2)
    @qml.qnode(dev,interface="autograd",diff_method="parameter-shift")
    def energy(t):
        qml.RY(t,wires=0)
        qml.CNOT(wires=[0,1])
        return qml.expval(.5*(qml.Z(0)+qml.Z(1))+.7*(qml.X(0)@qml.X(1)))
    t = qml.numpy.array(theta,requires_grad=True)
    return np.array([energy(t),qml.grad(energy)(t)])


TASKS = {
    "ghz": (ketary_ghz,qiskit_ghz,cirq_ghz,pennylane_ghz),
    "qft": (ketary_qft,qiskit_qft,cirq_qft,pennylane_qft),
    "bv": (ketary_bv,qiskit_bv,cirq_bv,pennylane_bv),
    "gradient": (ketary_gradient,qiskit_gradient,cirq_gradient,pennylane_gradient),
}
ROUTES = ("ketary","qiskit","cirq","pennylane")


def oracle(task,value):
    if task=="ghz":
        state=np.zeros(1<<value,dtype=complex)
        state[0]=state[-1]=2**-.5
        return state
    if task=="qft":
        return np.exp(2j*np.pi*np.arange(1<<value)/(1<<value))/np.sqrt(1<<value)
    if task=="bv":
        state=np.zeros(1<<(len(value)+1),dtype=complex)
        state[int(value,2)]=2**-.5
        state[int(value,2)+(1<<len(value))]=-2**-.5
        return state
    t=value
    return np.array([np.cos(t)+.7*np.sin(t),-np.sin(t)+.7*np.cos(t)])


def source_metrics(fn):
    source=inspect.getsource(fn)
    tree=ast.parse(source)
    ignored={tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,
             tokenize.COMMENT,tokenize.ENDMARKER}
    return {"source":source,
            "tokens":sum(t.type not in ignored for t in tokenize.generate_tokens(io.StringIO(source).readline)),
            "ast_nodes":sum(1 for _ in ast.walk(tree)),
            "calls":sum(isinstance(x,ast.Call) for x in ast.walk(tree)),
            "loops":sum(isinstance(x,(ast.For,ast.While,ast.comprehension)) for x in ast.walk(tree)),
            "loc":sum(bool(line.strip()) and not line.lstrip().startswith("#") for line in source.splitlines())}


def run(seed,reps):
    rng=random.Random(seed)
    cases=[]
    for task,values in (("ghz",(2,4,8,12)),("qft",(2,4,8)),("bv",("1","101","10110","10010101")),
                        ("gradient",(-1.1,0.0,.37,1.9))):
        for value in values:
            expected=oracle(task,value)
            functions=dict(zip(ROUTES,TASKS[task]))
            errors={}
            for route,fn in functions.items():
                actual=fn(value)
                np.testing.assert_allclose(actual,expected,atol=1e-9,rtol=0,
                                           err_msg=f"{route}/{task}/{value}")
                errors[route]=float(np.max(np.abs(actual-expected)))
            raw={r:[] for r in ROUTES}
            orders=[]
            for i in range(reps+3):
                order=list(ROUTES)
                rng.shuffle(order)
                if i>=3:
                    orders.append(order)
                for route in order:
                    start=time.perf_counter_ns()
                    result=functions[route](value)
                    elapsed=(time.perf_counter_ns()-start)/1e6
                    if i>=3:
                        raw[route].append(elapsed)
                    del result
            cases.append({"task":task,"value":value,"max_error":errors,"orders":orders,
                          "samples":{r:{"raw_ms":v,"median_ms":statistics.median(v),
                                        "p95_ms":float(np.percentile(v,95))} for r,v in raw.items()}})
    return {"scope":"authored examples, not independent user performance; end-to-end construction/device setup/output",
            "commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "seed":seed,"repetitions":reps,"cases":cases,
            "source_metrics":{task:{r:source_metrics(fn) for r,fn in zip(ROUTES,funcs)}
                              for task,funcs in TASKS.items()},
            "gradient_scope":{"ketary":"public occurrence-wise expectation Jacobian",
                              "qiskit":"authored two-shift native Statevector evaluation",
                              "cirq":"authored two-shift simulator expectation",
                              "pennylane":"public autograd parameter-shift QNode"},
            "versions":{"qiskit":qiskit.__version__,"cirq":cirq.__version__,
                        "pennylane":qml.__version__,"numpy":np.__version__}}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--repetitions",type=int,default=30)
    a=p.parse_args()
    if not 3<=a.repetitions<=100:
        p.error("3..100 repetitions")
    print(json.dumps(run(a.seed,a.repetitions),indent=2,allow_nan=False))
