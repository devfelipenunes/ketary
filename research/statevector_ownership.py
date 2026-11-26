"""Inspect native array ownership and actual defensive copy cost.

Do not infer exclusive ownership from OWNDATA of the base or from
shares_memory alone. No alternate simulator or installed adoption change.
"""
import argparse,json,random,time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit.quantum_info import Statevector
from research.native_stage_profile import stats

def describe(a,borrowed):
    chain=[];x=a;seen=set()
    while isinstance(x,np.ndarray) and id(x) not in seen:
        seen.add(id(x));chain.append(dict(shape=list(x.shape),strides=list(x.strides),
            owns=bool(x.flags.owndata),writeable=bool(x.flags.writeable),
            contiguous=bool(x.flags.c_contiguous),nbytes=x.nbytes))
        x=x.base
    return dict(chain=chain,terminal_base_type=type(x).__name__,
                aliases_input=bool(np.shares_memory(a,borrowed)))

def evaluate(n,kind,seed=1101,reps=7):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    source=q.Result(v);c=q.Circuit(n)
    if kind=="identity":pass
    elif kind=="local":c.ry(.31,0)
    elif kind=="far":c.cx(0,n-1)
    elif kind=="phase":c.evolve(q.I(),time=.31) if n<=8 else None
    elif kind=="mixed":c.ry(.31,n-1).cx(n-1,0).rz(-.47,0)
    else:raise ValueError("unknown case")
    if kind=="phase" and n>8:raise ValueError("phase fixture width")
    raw=c.to_qiskit()
    expected=Statevector(v).evolve(raw).data.copy()
    sample=Statevector(source._data).evolve(raw).data
    meta=describe(sample,source._data)
    samples={k:[] for k in ("evolution","private_result","public_copy","export")}
    adopted=0;error=0.
    for _ in range(reps):
        t=time.perf_counter_ns();a=Statevector(source._data).evolve(raw).data
        samples["evolution"].append((time.perf_counter_ns()-t)/1e6)
        t=time.perf_counter_ns();r=q.Result._from_evolution(a,borrowed=source._data)
        samples["private_result"].append((time.perf_counter_ns()-t)/1e6)
        adopted+=int(np.shares_memory(r._data,a))
        t=time.perf_counter_ns();copy=q.Result(a)
        samples["public_copy"].append((time.perf_counter_ns()-t)/1e6)
        t=time.perf_counter_ns();out=r.math.statevector()
        samples["export"].append((time.perf_counter_ns()-t)/1e6)
        error=max(error,float(np.max(np.abs(out-expected))))
        assert not np.shares_memory(r._data,source._data)
        assert not np.shares_memory(copy._data,a)
        out[:]=0
        np.testing.assert_array_equal(source.math.statevector(),v)
        np.testing.assert_allclose(r.math.statevector(),expected,atol=1e-9,rtol=0)
    assert error<1e-9
    return dict(n=n,kind=kind,seed=seed,ownership=meta,adopted=adopted,reps=reps,max_error=error,
                stages={k:stats(v) for k,v in samples.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,16):
        for kind in ("identity","local","far","phase","mixed"):
            if n>8 and kind=="phase":continue
            row=evaluate(n,kind,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="array flags/base chains, no proof of exclusive ownership or RSS",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
