"""Illustrative two-qubit H2-style active-space model; not molecular data."""
import argparse
import inspect
import json
import random
import time
import numpy as np
from scipy.optimize import minimize_scalar
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp,Statevector
import ketary as q
from research.circuit_rewrite_ladder import metrics,stats

TERMS={"II":-1.05,"ZI":.4,"IZ":.3,"ZZ":.12,"XX":.18,"YY":-.18}


def matrix():
    i=np.eye(2);x=np.array([[0,1],[1,0]]);y=np.array([[0,-1j],[1j,0]])
    z=np.diag([1.,-1.]);pauli=dict(I=i,X=x,Y=y,Z=z)
    return sum(w*np.kron(pauli[p[0]],pauli[p[1]]) for p,w in TERMS.items())


def ketary_path():
    p=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(p,0).cx(0,1)
    h=q.Observable(TERMS)
    def state(theta):
        return c.bind({p:float(theta)}).run()
    def objective(theta):
        return state(theta).math.expectation(h)
    return c.to_qiskit(),objective,lambda theta:state(theta).math.statevector()


def native_path():
    p=Parameter("theta")
    c=QuantumCircuit(2);c.ry(p,0);c.cx(0,1)
    h=SparsePauliOp.from_list(list(TERMS.items()))
    def state(theta):
        return Statevector.from_instruction(c.assign_parameters({p:float(theta)}))
    def objective(theta):
        return float(state(theta).expectation_value(h).real)
    return c,objective,lambda theta:state(theta).data.copy()


def expected_state(theta):
    return np.array([np.cos(theta/2),0.,0.,np.sin(theta/2)],complex)


def evaluate(seed=1101,reps=3):
    if reps<1:raise ValueError("positive repetitions required")
    rng=random.Random(seed);H=matrix()
    ground=float(np.linalg.eigvalsh(H)[0])
    even=float(np.linalg.eigvalsh(H[np.ix_([0,3],[0,3])])[0])
    assert abs(ground-even)<1e-12
    routes={"ketary":ketary_path,"qiskit":native_path};rows={}
    angles=[rng.uniform(-np.pi,np.pi) for _ in range(5)]
    for name,build in routes.items():
        c,objective,state=build()
        for theta in angles:
            expected=expected_state(theta)
            np.testing.assert_allclose(state(theta),expected,atol=1e-9,rtol=0)
            np.testing.assert_allclose(objective(theta),np.vdot(expected,H@expected).real,atol=1e-9,rtol=0)
        text=inspect.getsource(build)
        rows[name]=dict(source=text,source_metrics=metrics(text),logical_gates=len(c.data),depth=c.depth(),build_ms=[],optimize_ms=[],histories=[])
    for _ in range(reps):
        for name in rng.sample(list(routes),len(routes)):
            start=time.perf_counter_ns();_,objective,state=routes[name]();mid=time.perf_counter_ns()
            history=[]
            def cost(theta):
                value=float(objective(theta));history.append([float(theta),value]);return value
            result=minimize_scalar(cost,bounds=(-np.pi,np.pi),method="bounded",options={"xatol":1e-10,"maxiter":100})
            end=time.perf_counter_ns()
            assert result.success and abs(result.fun-ground)<1e-8
            vector=state(result.x)
            np.testing.assert_allclose(vector,expected_state(result.x),atol=1e-9,rtol=0)
            assert abs(np.vdot(vector,H@vector).real-ground)<1e-8
            rows[name]["build_ms"].append((mid-start)/1e6)
            rows[name]["optimize_ms"].append((end-mid)/1e6)
            rows[name]["histories"].append(dict(points=history,nfev=int(result.nfev),energy=float(result.fun),theta=float(result.x)))
    for row in rows.values():
        for key in ("build_ms","optimize_ms"):row[key]=stats(row[key])
    return dict(seed=seed,ground=ground,even_ground=even,paths=rows,scope="illustrative model; same optimizer and objective; no molecular accuracy, external author or controlled host claim")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=3);args=p.parse_args()
    if args.reps<1:p.error("positive repetitions required")
    print(json.dumps([evaluate(seed,args.reps) for seed in (1101,2202,3303)],indent=2,allow_nan=False))
