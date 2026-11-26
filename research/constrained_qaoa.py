"""Three bounded synthetic constrained optimization programs with paired routes.

These are authored applications, not evidence of quantum advantage or user studies.
"""
import argparse
import itertools
import json
from pathlib import Path
import time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

N=4
EDGES=((0,1),(1,2),(2,3),(3,0))
WEIGHTS=(1,2,1,2)
RETURNS=(6,4,5,7)
RISK=(2,2,1,5)
PAIRS=((0,2,3),(1,3,1),(0,1,1))
KINDS=("independent_set","vertex_cover","portfolio")

def objective(kind,x):
    if kind=="independent_set":
        return -sum(w*b for w,b in zip(WEIGHTS,x))+5*sum(x[i]*x[j] for i,j in EDGES)
    if kind=="vertex_cover":
        return sum(w*b for w,b in zip(WEIGHTS,x))+5*sum((1-x[i])*(1-x[j]) for i,j in EDGES)
    if kind=="portfolio":
        return (sum((r-v)*b for r,v,b in zip(RISK,RETURNS,x))
                +sum(w*x[i]*x[j] for i,j,w in PAIRS)+20*(sum(x)-2)**2)
    raise ValueError("unknown objective")

def feasible(kind,x):
    if kind=="independent_set":return all(not (x[i] and x[j]) for i,j in EDGES)
    if kind=="vertex_cover":return all(x[i] or x[j] for i,j in EDGES)
    if kind=="portfolio":return sum(x)==2
    raise ValueError("unknown objective")

def evaluate(kind):
    # Enumerate bit strings in native little-endian integer order.
    bits=[tuple((k>>i)&1 for i in range(N)) for k in range(1<<N)]
    costs=np.array([objective(kind,x) for x in bits],float)
    valid=np.array([feasible(kind,x) for x in bits])
    optimum=float(min(costs))
    winners=np.flatnonzero(costs==optimum)
    assert all(valid[winners])
    assert optimum==float(min(costs[valid]))
    # Exact finite Walsh transform, independent from circuit construction.
    coeff={}
    for mask in range(1<<N):
        v=sum(c*(-1)**((mask&k).bit_count()) for k,c in enumerate(costs))/(1<<N)
        if v:
            assert mask.bit_count()<=2
            coeff[mask]=float(v)
    labels={''.join('Z' if mask&(1<<i) else 'I' for i in reversed(range(N))):v
            for mask,v in coeff.items()}
    H=q.Observable(labels)
    diagonal=np.array([sum(v*(-1)**((mask&k).bit_count()) for mask,v in coeff.items())
                       for k in range(1<<N)])
    np.testing.assert_array_equal(diagonal,costs)

    def ketary(g,b):
        return q.Circuit(N).h(range(N)).evolve(H,time=g).rx(2*b,range(N)).run().math.statevector()
    def native(g,b):
        c=QuantumCircuit(N);c.h(range(N))
        for mask,v in coeff.items():
            wires=[i for i in range(N) if mask&(1<<i)]
            if not wires:c.global_phase-=g*v
            elif len(wires)==1:c.rz(2*g*v,wires[0])
            else:c.rzz(2*g*v,*wires)
        c.rx(2*b,range(N))
        return Statevector.from_instruction(c).data.copy()
    def independent(g,b):
        rx=np.array([[np.cos(b),-1j*np.sin(b)],[-1j*np.sin(b),np.cos(b)]])
        mix=np.ones((1,1),complex)
        for _ in range(N):mix=np.kron(mix,rx)
        return mix@(np.exp(-1j*g*costs)/np.sqrt(1<<N))

    rows=[]
    for index,(g,b) in enumerate(itertools.product((0.,.13,.31,.7,1.1),(0.,.2,.45,.8,1.3))):
        expected=independent(g,b)
        out={};timings={}
        routes=[("ketary",ketary),("qiskit",native)]
        if index%2:routes.reverse()
        for name,fn in routes:
            start=time.perf_counter_ns();out[name]=fn(g,b)
            timings[name]=(time.perf_counter_ns()-start)/1e6
            np.testing.assert_allclose(out[name],expected,atol=1e-9,rtol=0)
        prob=np.abs(expected)**2
        energy=float(prob@costs)
        assert energy>=optimum-1e-9
        rows.append(dict(gamma=g,beta=b,energy=energy,
            feasible_probability=float(sum(prob[valid])),
            optimal_probability=float(sum(prob[winners])),
            max_state_residual=max(float(np.max(np.abs(v-expected))) for v in out.values()),
            raw_ms=timings,order=[name for name,_ in routes]))
    best=min(rows,key=lambda row:row["energy"])
    assert best["energy"]<=float(np.mean(costs))+1e-9
    return dict(kind=kind,qubits=N,exact_classical_minimum=optimum,
                optimum_labels=[format(int(k),"04b") for k in winners],
                feasible_assignments=int(valid.sum()),grid_best=best,rows=rows,
                scope="fixed finite grid, authored synthetic problem, no continuous optimum or speedup claim")

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    results=[evaluate(kind) for kind in KINDS]
    args.output.write_text(json.dumps(results,indent=2,allow_nan=False))
    for result in results:print(json.dumps(result),flush=True)

if __name__=="__main__":main()
