"""Trace snapshot ownership and allocation research, not SDK dispatch."""
import argparse,json,random,statistics,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ketary as q
from ketary import _trace
from research.trace_wire_index_rss import fixture

Original=_trace._Cursor
class AdoptCursor(Original):
    """Consume fresh output only; retain conservative snapshot fallback."""
    def at(self,index):
        while self.index<index:
            item=self.qc.data[self.index]
            self.wires=tuple(self.qc.find_bit(w).index for w in item.qubits)
            self.operation=item.operation.name
            self.state=self.state.evolve(item.operation,qargs=list(self.wires))
            self.index+=1
        # Always keep the current native state on its own storage. A fresh
        # contiguous owning output may be adopted by Result only when the
        # cursor is finished; intermediate states may still be read/evolved.
        # In this diagnostic the final step is known and never advanced.
        if index==len(self.qc.data):
            return _trace.TraceStep(self.operation,self.wires,q.Result._from_evolution(self.state.data))
        return _trace.TraceStep(self.operation,self.wires,q.Result(self.state.data))

def evaluate(n,count,reps):
    if not 3<=reps<=100:raise ValueError("repetitions must be 3..100")
    c=fixture(n,count);raw=c.to_qiskit()
    variants={"current":Original,"terminal_adoption":AdoptCursor}
    expected=c.debug.trace()
    samples={k:[] for k in variants};orders=[];rng=random.Random(n+count)
    for name,cursor in variants.items():
        with patch.object(_trace,"_Cursor",cursor):out=c.debug.trace()
        for a,b in zip(expected,out,strict=True):
            assert a.operation==b.operation and a.wires==b.wires
            np.testing.assert_array_equal(a.result.math.statevector(),b.result.math.statevector())
        for i,step in enumerate(out):
            for other in out[i+1:]:
                assert not np.shares_memory(step.result._data,other.result._data)
        export=out[-1].result.math.statevector();export[:]=0
        np.testing.assert_array_equal(out[-1].result.math.statevector(),expected[-1].result.math.statevector())
    for i in range(reps+3):
        order=list(variants);rng.shuffle(order)
        if i>=3:orders.append(order)
        for name in order:
            with patch.object(_trace,"_Cursor",variants[name]):
                start=time.perf_counter_ns();out=c.debug.trace();dt=(time.perf_counter_ns()-start)/1e6
            if i>=3:samples[name].append(dt)
            del out
    assert c.to_qiskit()==raw
    return dict(n=n,count=count,orders=orders,
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=20)
    a=p.parse_args();rows=[]
    for n in (4,8):
        for count in (32,128,256):
            row=evaluate(n,count,a.repetitions);rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="terminal-only snapshot adoption; full public trace only; no runtime change",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
