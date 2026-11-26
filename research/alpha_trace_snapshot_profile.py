"""Matched old/new cursor paths; no changed trace payload contract."""
import argparse
import json
import random
import time
import numpy as np
import ketary as q
from ketary._trace import _Cursor,TraceStep
from research.circuit_rewrite_ladder import stats

class Baseline(_Cursor):
    def at(self,index):
        while self.index<index:
            item=self.qc.data[self.index]
            self.wires=tuple(self.qc.find_bit(w).index for w in item.qubits)
            self.operation=item.operation.name
            self.state=self.state.evolve(item.operation,qargs=list(self.wires))
            self.index+=1
        return TraceStep(self.operation,self.wires,q.Result(self.state.data))

def run(seed,reps):
    rng=random.Random(seed)
    rows=[]
    for n,depth in ((4,4),(8,4),(8,12)):
        c=q.Circuit(n)
        for _ in range(depth):
            for i in range(n):c.ry(rng.uniform(-1,1),i)
            for i in range(n-1):c.cx(i,i+1)
        count=len(c._qc.data)
        def collect(cls):
            cursor=cls(c)
            return tuple(cursor.at(i) for i in range(count+1))
        routes={"baseline":lambda:collect(Baseline),"candidate":lambda:collect(_Cursor)}
        expected=routes["baseline"]()
        timings={k:[] for k in routes}
        for _ in range(reps):
            for k in rng.sample(list(routes),len(routes)):
                t=time.perf_counter_ns();actual=routes[k]();dt=(time.perf_counter_ns()-t)/1e6
                for a,b in zip(actual,expected,strict=True):
                    assert (a.operation,a.wires)==(b.operation,b.wires)
                    np.testing.assert_array_equal(a.result._data,b.result._data)
                timings[k].append(dt)
        rows.append(dict(n=n,operations=count,seed=seed,paths={k:stats(v) for k,v in timings.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"identical retained prefix snapshots; shared CI, no RSS claim","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
