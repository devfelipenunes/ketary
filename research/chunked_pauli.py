"""Research-only bounded chunked Pauli action; compare existing streamed path.

Little-endian input basis j maps to j XOR xmask. The phase is
i**number_of_Y times (-1)**parity(j & zmask), with Z and Y in zmask.
No dense operator or whole-state index array. Chunk size is explicit.
"""
import argparse,json,random,time
from pathlib import Path
import numpy as np
import ketary as q
from ketary._validation import _int,_real,_limit
from research.query_plan_cost import stats

def masks(label):
    x=z=y=0
    for i,axis in enumerate(reversed(label)):
        if axis in "XY":x|=1<<i
        if axis in "YZ":z|=1<<i
        if axis=="Y":y+=1
    return x,z,1j**y

def variance(r,H,*,chunk=4096,max_bytes=64*1024**2,max_work=1<<25):
    if not isinstance(r,q.Result) or not isinstance(H,q.Observable):
        raise TypeError("expected Result and Observable")
    n=r.num_qubits;size=1<<n
    chunk=min(size,_int(chunk,1),65536)
    terms=H.to_dict(n)
    _limit(n,4,budget=max_bytes)
    if len(terms)*n*size>_int(max_work,1):raise q.ResourceLimit("Pauli application work limit exceeded")
    # Separate conservative chunk scratch guard within the research path.
    # Includes index, parity, sign, gather and multiplication arrays.
    if 32*size+96*chunk>max_bytes:raise q.ResourceLimit("research scratch estimate exceeds budget")
    state=r._data/np.sqrt(r._norm_sq)
    out=np.zeros_like(state)
    for label,coefficient in terms.items():
        if not coefficient:continue
        x,z,phase=masks(label)
        for start in range(0,size,chunk):
            j=np.arange(start,min(start+chunk,size),dtype=np.int64)
            p=j&z
            # XOR folding computes parity without a NumPy-version-specific popcount.
            p^=p>>32;p^=p>>16;p^=p>>8;p^=p>>4;p^=p>>2;p^=p>>1
            sign=1-2*(p&1)
            out[j^x]+=coefficient*phase*sign*state[j]
    delta=out-np.vdot(state,out)*state
    value=float(np.vdot(delta,delta).real)
    if not np.isfinite(value):raise ArithmeticError("observable variance is not finite")
    return value

def previous(r,H):
    from qiskit.quantum_info import Statevector
    from qiskit.circuit.library import XGate,YGate,ZGate
    gates={"X":XGate(),"Y":YGate(),"Z":ZGate()}
    state=r._data/np.sqrt(r._norm_sq);out=np.zeros_like(state)
    for label,coefficient in H.to_dict(r.num_qubits).items():
        term=Statevector(state)
        for wire,axis in enumerate(reversed(label)):
            if axis!="I":term=term.evolve(gates[axis],qargs=[wire])
        out+=coefficient*term.data
    delta=out-np.vdot(state,out)*state
    return float(np.vdot(delta,delta).real)

def evaluate(n,count,seed=1101,reps=7):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    r=q.Result(v)
    terms={}
    while len(terms)<count:
        label="".join(rng.choice(list("IXYZ"),size=n));terms[label]=float(rng.uniform(-1,1))
    H=q.Observable(terms)
    routes={"streamed":lambda:previous(r,H),
            "chunked":lambda:variance(r,H),
            "installed":lambda:r.math.observable_variance_streamed(H)}
    reference=routes["streamed"]()
    if n<=8:
        raw=H.to_qiskit(n).to_matrix();hv=raw@v
        want=float(np.vdot(hv-np.vdot(v,hv)*v,hv-np.vdot(v,hv)*v).real)
        assert abs(want-reference)<1e-9
    error=abs(reference-routes["chunked"]());assert error<1e-9
    samples={k:[] for k in routes};rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(routes),len(routes)):
            t=time.perf_counter_ns();value=routes[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
            assert abs(value-reference)<1e-9
    return dict(n=n,terms=count,seed=seed,max_error=error,variants={k:stats(v) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,12,16):
        for count in (4,16):
            row=evaluate(n,count,a.seed,5);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="legacy native path, research and installed chunked Pauli variance; shared CI, no peak RSS claim",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
