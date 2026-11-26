"""Issue #276: explicit copy, logical replay, binding and snapshot inventory."""
import argparse,json,random,statistics,subprocess,sys,time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit.quantum_info import Statevector
from research.performance_memory_closure import own_memory

def fixture(n,layers):
    if n not in (4,8,12) or layers not in (4,32):raise ValueError("unsupported workload")
    p=q.Circuit.parameter_vector("t",n)
    template=q.Circuit.symbolic(n)
    for i in range(layers):
        template.ry([x*(i+1)/layers for x in p],range(n))
        template.cx(pairs=q.chain(range(n)))
    values=dict(zip(p,[.2+i*.017 for i in range(n)],strict=True))
    bound=template.bind(values)
    return template,values,bound

def worker(n,layers,kind,reps):
    if not 3<=reps<=30:raise ValueError("bounded repetition count")
    template,values,c=fixture(n,layers)
    raw=c.to_qiskit();payload=c.to_json();r=c.run()
    # All routes receive identical prepared inputs; baseline includes them.
    routes={"copy":c.copy,"native_export":c.to_qiskit,"encode":c.to_json,
            "decode":lambda:q.Circuit.from_json(payload),
            "bind":lambda:template.bind(values),"run":c.run,
            "snapshot_export":r.math.statevector}
    fn=routes[kind];before=own_memory();samples=[]
    for _ in range(reps):
        t=time.perf_counter_ns();out=fn();samples.append((time.perf_counter_ns()-t)/1e6)
        if _<reps-1:del out
    after=own_memory()
    retained={"native_instruction_count":None,"serialized_utf8_bytes":None,"array_payload_bytes":None}
    if kind in ("copy","decode","bind"):
        assert out.to_qiskit()==raw
        retained["native_instruction_count"]=len(raw.data)
        out.x(0);assert c.to_qiskit()==raw
    elif kind=="native_export":
        assert out==raw;retained["native_instruction_count"]=len(out.data)
        out.x(0);assert c.to_qiskit()==raw
    elif kind=="encode":
        assert out==payload;retained["serialized_utf8_bytes"]=len(out.encode("utf-8"))
        assert q.Circuit.from_json(out).to_qiskit()==raw
    elif kind in ("run","snapshot_export"):
        got=out.math.statevector() if kind=="run" else out
        expected=Statevector.from_instruction(raw).data
        np.testing.assert_allclose(got,expected,atol=1e-9,rtol=0)
        retained["array_payload_bytes"]=got.nbytes
        got[:]=0
        np.testing.assert_allclose(r.math.statevector(),expected,atol=1e-9,rtol=0)
        if kind=="run":np.testing.assert_allclose(out.math.statevector(),expected,atol=1e-9,rtol=0)
    assert template.bind(values).to_qiskit()==raw and c.to_json()==payload
    return dict(n=n,layers=layers,gates=len(raw.data),kind=kind,before=before,after=after,
                retained=retained,raw_ms=samples,p50_ms=statistics.median(samples),p95_ms=float(np.quantile(samples,.95)),verified=True)

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path);p.add_argument("--worker",action="store_true")
    p.add_argument("--n",type=int);p.add_argument("--layers",type=int)
    p.add_argument("--kind",choices=("copy","native_export","encode","decode","bind","run","snapshot_export"))
    p.add_argument("--repetitions",type=int,default=7);a=p.parse_args()
    if a.worker:print(json.dumps(worker(a.n,a.layers,a.kind,a.repetitions),allow_nan=False));return
    if not a.output:p.error("output required")
    rows=[]
    for n,layers in ((4,4),(8,32),(12,32)):
        for rep in range(3):
            kinds=["copy","native_export","encode","decode","bind","run","snapshot_export"]
            random.Random(n+layers+rep).shuffle(kinds)
            for kind in kinds:
                cmd=[sys.executable,"-m","research.copy_replay_inventory","--worker","--n",str(n),"--layers",str(layers),"--kind",kind,"--repetitions",str(a.repetitions)]
                row=dict(rep=rep,**json.loads(subprocess.check_output(cmd,text=True,timeout=90)))
                rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="isolated Linux HWM; retained output payload separately, not native heap size or exact allocation count; preparation excluded from timer",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
