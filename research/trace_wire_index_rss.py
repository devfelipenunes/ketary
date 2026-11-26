"""Trace stage attribution and isolated Linux process high-water RSS."""
import argparse,json,random,statistics,subprocess,sys,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from ketary import _trace
from research.expressive_composition_cost import workload as composition_workload,_one_staged_copy

OriginalCursor=_trace._Cursor

class IndexedCursor(OriginalCursor):
    """Call-local wire map; identical defensive snapshot construction."""
    def __init__(self,c):
        super().__init__(c)
        self._wire_index={wire:i for i,wire in enumerate(self.qc.qubits)}

    def at(self,index):
        while self.index<index:
            item=self.qc.data[self.index]
            self.wires=tuple(self._wire_index[w] for w in item.qubits)
            self.operation=item.operation.name
            self.state=self.state.evolve(item.operation,qargs=list(self.wires))
            self.index+=1
        return _trace.TraceStep(self.operation,self.wires,q.Result(self.state.data))

def fixture(n,count):
    if n not in (4,8) or count not in (32,128,256):
        raise ValueError("unsupported workload")
    raw=QuantumCircuit(n,global_phase=.37)
    for i in range(count):
        w=i%n
        if i%4==0:raw.h(w)
        elif i%4==1:raw.ry(.013*(i%13),w)
        elif i%4==2:raw.cx(w,(w+1)%n)
        else:raw.rz(-.21,w)
    return q.from_qiskit(raw)

def evaluate(n,count,reps):
    if not 3<=reps<=100:raise ValueError("repetitions must be 3..100")
    c=fixture(n,count);raw=c.to_qiskit()
    initial=np.zeros(1<<n,complex);initial[0]=np.exp(1j*float(raw.global_phase))
    state=Statevector(initial)
    expected=[state.data.copy()]
    for item in raw.data:
        state=state.evolve(item.operation,qargs=[raw.find_bit(w).index for w in item.qubits])
        expected.append(state.data.copy())
    variants={"current":OriginalCursor,"indexed":IndexedCursor}
    errors={}
    for key,cursor in variants.items():
        with patch.object(_trace,"_Cursor",cursor):
            steps=c.debug.trace()
        values=[step.result.math.statevector() for step in steps]
        np.testing.assert_allclose(values,expected,atol=1e-9,rtol=0)
        errors[key]=float(np.max(np.abs(np.asarray(values)-expected)))
    assert c.to_qiskit()==raw
    samples={k:[] for k in variants};orders=[];rng=random.Random(n+count)
    for i in range(reps+3):
        order=list(variants);rng.shuffle(order)
        if i>=3:orders.append(order)
        for key in order:
            with patch.object(_trace,"_Cursor",variants[key]):
                start=time.perf_counter_ns();steps=c.debug.trace();elapsed=(time.perf_counter_ns()-start)/1e6
            if i>=3:samples[key].append(elapsed)
            del steps
    return dict(n=n,count=count,errors=errors,orders=orders,
                scope="same trace public path and snapshots, only cursor wire lookup differs",
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def memory():
    fields={}
    with open("/proc/self/status",encoding="utf-8") as f:
        for line in f:
            if line.startswith(("VmRSS:","VmHWM:")):
                k,v=line.split(":",1);fields[k]=int(v.split()[0])
    return {"current_kib":fields["VmRSS"],"peak_kib":fields["VmHWM"]}

def worker(kind,variant):
    """One workload in a separate process. Retain outputs at observation."""
    if kind=="trace":
        c=fixture(8,256)
        cursor={"current":OriginalCursor,"candidate":IndexedCursor}[variant]
        before=memory()
        with patch.object(_trace,"_Cursor",cursor):
            out=c.debug.trace()
        after=memory()
        assert len(out)==257
        out[-1].result.test.state(c.run(),ignore_global_phase=False).require()
        payload=257*(16*(1<<8))
    elif kind=="composition":
        c,u,v,cw,aw=composition_workload(10000)
        before=memory()
        if variant=="current":out=c.compute_action_uncompute(u,v,compute_wires=cw,action_wires=aw)
        elif variant=="candidate":out=_one_staged_copy(c,u,v,cw,aw)
        else:raise ValueError("unknown variant")
        after=memory()
        assert len(out.to_qiskit().data)==10005
        payload=None
    else:raise ValueError("unknown workload")
    return dict(kind=kind,variant=variant,before=before,after=after,payload_bytes=payload,
                scope="Linux isolated process VmHWM; includes Python/native allocator and imports")

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path)
    p.add_argument("--worker",choices=("trace","composition"));p.add_argument("--variant",choices=("current","candidate"))
    p.add_argument("--repetitions",type=int,default=20)
    a=p.parse_args()
    if a.worker:
        if not a.variant:p.error("--variant required")
        print(json.dumps(worker(a.worker,a.variant),allow_nan=False));return
    if not a.output:p.error("--output required")
    rows=[evaluate(n,k,a.repetitions) for n in (4,8) for k in (32,128,256)]
    memory_rows=[]
    if sys.platform.startswith("linux"):
        for kind in ("trace","composition"):
            for rep in range(3):
                for variant in (("current","candidate") if rep%2==0 else ("candidate","current")):
                    cmd=[sys.executable,"-m","research.trace_wire_index_rss","--worker",kind,"--variant",variant]
                    row=json.loads(subprocess.check_output(cmd,text=True,timeout=90))
                    memory_rows.append(dict(rep=rep,**row))
    for row in rows:print(json.dumps(row,allow_nan=False),flush=True)
    for row in memory_rows:print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(timing=rows,rss=memory_rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
