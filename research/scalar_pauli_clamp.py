"""Paired public paths with exact previous scalar numeric acceptance."""
import argparse,json,math,random,statistics,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ketary as q
from qiskit.quantum_info import Pauli
from research.pauli_query_attribution import workload,independent

def previous(self,state,label):
    value=complex(state.expectation_value(Pauli(label)))
    if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value.imag)>1e-9:
        raise ArithmeticError("invalid Hermitian Pauli expectation")
    return float(np.clip(value.real/self._r._norm_sq,-1,1))

def evaluate(n,count,reps):
    if not 3<=reps<=100:raise ValueError("repetitions must be 3..100")
    data,labels=workload(n,count,1201)
    r=q.Result(data);cls=type(r.math);candidate=cls._native_pauli_value
    want=tuple(independent(data,label) for label in labels)
    # Exercise the same real grouped public method in both routes.
    # Additional scalar case uses the same one-label public method.
    query=(lambda:r.math.expectation(labels[0])) if count==1 else (lambda:r.math.expectations(labels))
    if count==1:want=want[0]
    for fn in (previous,candidate):
        with patch.object(cls,"_native_pauli_value",fn):
            np.testing.assert_allclose(query(),want,atol=1e-9,rtol=0)
    samples={"previous":[],"candidate":[]};orders=[];rng=random.Random(1201+n+count)
    for i in range(reps+3):
        order=list(samples);rng.shuffle(order)
        if i>=3:orders.append(order)
        for name in order:
            with patch.object(cls,"_native_pauli_value",previous if name=="previous" else candidate):
                start=time.perf_counter_ns();query();elapsed=(time.perf_counter_ns()-start)/1e6
            if i>=3:samples[name].append(elapsed)
    np.testing.assert_array_equal(r.math.statevector(),data)
    return dict(n=n,count=count,scope="same public path, previous numeric body patched outside timer; single-thread research only",
                orders=orders,variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=30)
    a=p.parse_args();rows=[evaluate(n,k,a.repetitions) for n in (4,8,12) for k in (1,8,32)]
    for row in rows:print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(rows,indent=2,allow_nan=False))
if __name__=="__main__":main()
