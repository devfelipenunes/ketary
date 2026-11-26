"""Stage attribution, not a general backend comparison.

Each route uses the same symbolic template and nonzero complex input.
Independent Qiskit construction and complete small operator equality.
Private stage timings are diagnostic, not a sum of end-to-end medians.
"""
import argparse,contextlib,io,json,platform,random,statistics,time
from pathlib import Path
from importlib.metadata import version
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector,Operator
from ketary._adapter import _validate_bound_values
from ketary._validation import _angle

def timed(fn):
    t=time.perf_counter_ns();out=fn();return out,(time.perf_counter_ns()-t)/1e6
def stats(a):
    return dict(raw_ms=a,p50_ms=statistics.median(a),p95_ms=float(np.quantile(a,.95)))
def evaluate(n,layers,seed=1101,reps=7):
    rng=np.random.default_rng(seed)
    p=q.Circuit.parameter_vector("p",n)
    row=rng.uniform(-.8,.8,n).tolist()
    def ketary_build():
        c=q.Circuit.symbolic(n)
        for k in range(layers):
            c.ry([p[i]*(k+1)/layers for i in range(n)],range(n)).cx(pairs=q.chain(range(n)))
        return c
    def native_build():
        c=QuantumCircuit(n)
        for k in range(layers):
            for i in range(n):c.ry(p[i]*(k+1)/layers,i)
            c.cx(list(range(n-1)),list(range(1,n)))
        return c
    template=ketary_build();raw=native_build()
    assert raw==template.to_qiskit()
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    borrowed=q.Result(v);bindings=dict(zip(p,row,strict=True))
    bound=template.bind(bindings)
    native=raw.assign_parameters(bindings,inplace=False,flat_input=True)
    assert native==bound.to_qiskit()
    expected=Statevector(v).evolve(native).data.copy()
    np.testing.assert_allclose(bound.run(initial_state=borrowed).math.statevector(),expected,atol=1e-9,rtol=0)
    if n<=6:np.testing.assert_allclose(Operator(native).data,Operator(bound.to_qiskit()).data,atol=1e-9,rtol=0)
    stages={k:[] for k in ("ketary_build","native_build","ketary_bind","native_bind","binding_preflight","native_assign","bound_value_validation","native_evolve","result_adoption","result_public_copy","ketary_run","result_export")}
    rnd=random.Random(seed);adopted=0;error=0.
    for _ in range(reps):
        for k in rnd.sample(["ketary_build","native_build","ketary_bind","native_bind","ketary_run"],5):
            fn={"ketary_build":ketary_build,"native_build":native_build,
                "ketary_bind":lambda:template.bind(bindings),
                "native_bind":lambda:raw.assign_parameters(bindings,inplace=False,flat_input=True),
                "ketary_run":lambda:bound.run(initial_state=borrowed)}[k]
            out,ms=timed(fn);stages[k].append(ms)
            if k=="ketary_run":
                error=max(error,float(np.max(np.abs(out.math.statevector()-expected))))
        def preflight():
            assert set(bindings)==set(template._qc.parameters)
            return {key:_angle(value) for key,value in bindings.items()}
        numeric,ms=timed(preflight);stages["binding_preflight"].append(ms)
        assigned,ms=timed(lambda:template._qc.assign_parameters(numeric,inplace=False,flat_input=True));stages["native_assign"].append(ms)
        _,ms=timed(lambda:_validate_bound_values(assigned));stages["bound_value_validation"].append(ms)
        evolved,ms=timed(lambda:Statevector(borrowed._data).evolve(assigned).data);stages["native_evolve"].append(ms)
        # Adoption consumes a fresh private output; do not reuse a frozen array.
        result,ms=timed(lambda:q.Result._from_evolution(evolved,borrowed=borrowed._data));stages["result_adoption"].append(ms)
        adopted+=int(np.shares_memory(result._data,evolved))
        copied,ms=timed(lambda:q.Result(evolved));stages["result_public_copy"].append(ms)
        exported,ms=timed(result.math.statevector);stages["result_export"].append(ms)
        error=max(error,float(np.max(np.abs(exported-expected))),float(np.max(np.abs(copied.math.statevector()-expected))))
        assert not np.shares_memory(exported,result._data)
        assert not np.shares_memory(copied._data,evolved)
        np.testing.assert_array_equal(borrowed.math.statevector(),v)
    assert error<1e-9 and template.to_qiskit()==raw
    return dict(n=n,layers=layers,gates=len(raw.data),seed=seed,max_error=error,
                adoption_count=adopted,repetitions=reps,
                stages={k:stats(v) for k,v in stages.items()})
def environment():
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):
        np.show_config()
        np.show_runtime()
    return dict(python=platform.python_version(),qiskit=version("qiskit"),numpy=np.__version__,
                machine=platform.machine(),numpy_config_runtime=stream.getvalue())
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,12):
        for layers in (4,16,64):
            row=evaluate(n,layers,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="shared CI staged diagnostic; medians not additive; no dedicated RSS",environment=environment(),rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
