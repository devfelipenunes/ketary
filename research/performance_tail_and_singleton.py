"""Full one-item grouped path and composition tail follow-up."""
import argparse,json,math,random,statistics,time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ketary as q
from ketary._validation import _int,ResourceLimit
from research.pauli_query_attribution import independent,workload
from research.expressive_composition_cost import evaluate as composition_evaluate

# Exact previous method bodies from c97f8cf5, before call-local handle reuse;
# only import qualification and function names differ.
def previous_expectation(self,pauli):
    """Expectation of a Hermitian Pauli string, leftmost character is q[n-1]."""
    from ketary._observable import Observable
    if isinstance(pauli,Observable):
        return self.observable(pauli.to_dict(self._r._n))
    from ketary._validation import _pauli_label
    pauli=_pauli_label(self._r._n,pauli)
    if not isinstance(pauli,str) or len(pauli)!=self._r._n or any(p not in "IXYZ" for p in pauli):
        raise ValueError("expected a full-width uppercase I/X/Y/Z Pauli label")
    from qiskit.quantum_info import Pauli, Statevector
    # Native Pauli evaluation operates on the snapshot, not a dense operator.
    value=complex(Statevector(self._r._data).expectation_value(Pauli(pauli)))
    if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value.imag)>1e-9:
        raise ArithmeticError("invalid Hermitian Pauli expectation")
    return float(np.clip(value.real/self._r._norm_sq,-1,1))

def previous_expectations(self,observables,*,max_work=64*1024**2):
    """Ordered real expectations; validate first, reuse unique Pauli terms."""
    from collections.abc import Mapping
    from itertools import islice
    from ketary._observable import Observable
    from ketary._validation import _pauli_label
    work=_int(max_work,1)
    if isinstance(observables,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected an ordered iterable of observables")
    try:
        items=tuple(islice(iter(observables),33))
    except TypeError as exc:
        raise ValueError("expected an ordered iterable of observables") from exc
    if not items or len(items)>32:
        raise ResourceLimit("expectations requires 1..32 observables")
    n=self._r._n
    rows=[]
    labels=set()
    for item in items:
        if isinstance(item,Observable):
            terms=item.to_dict(n)
        else:
            label=_pauli_label(n,item)
            if not isinstance(label,str) or len(label)!=n or any(p not in "IXYZ" for p in label):
                raise ValueError("expected a full-width uppercase I/X/Y/Z Pauli label")
            terms={label:1.0}
        row=tuple(terms.items())
        rows.append(row)
        labels.update(terms)
    if len(labels)*self._r._data.size>work:
        raise ResourceLimit("grouped expectation work exceeds Pauli-state entry budget")
    cache={label:self.expectation(label) for label in sorted(labels)}
    values=tuple(math.fsum(coefficient*cache[label] for label,coefficient in row) for row in rows)
    if not all(math.isfinite(value) for value in values):
        raise ArithmeticError("observable expectation is not finite")
    return values

def singleton(n,reps,seed):
    if not 3<=reps<=100:raise ValueError("repetitions must be 3..100")
    data,labels=workload(n,1,seed);r=q.Result(data);cls=type(r.math)
    expected=(independent(data,labels[0]),)
    old=(previous_expectation,previous_expectations)
    new=(cls.expectation,cls.expectations)
    def route(methods):
        stack=ExitStack()
        for name,fn in zip(("expectation","expectations"),methods,strict=True):
            stack.enter_context(patch.object(cls,name,fn))
        return stack
    routes={"previous":old,"candidate":new}
    for methods in routes.values():
        with route(methods):np.testing.assert_allclose(r.math.expectations(labels),expected,atol=1e-9,rtol=0)
    samples={k:[] for k in routes};orders=[];rng=random.Random(seed+n)
    for i in range(reps+3):
        order=list(routes);rng.shuffle(order)
        if i>=3:orders.append(order)
        for name in order:
            with route(routes[name]):
                t=time.perf_counter_ns();r.math.expectations(labels);dt=(time.perf_counter_ns()-t)/1e6
            if i>=3:samples[name].append(dt)
    np.testing.assert_array_equal(r.math.statevector(),data)
    return dict(n=n,seed=seed,orders=orders,variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=30)
    a=p.parse_args()
    queries=[singleton(n,a.repetitions,seed) for n in (4,8,12) for seed in (1101,2202,3303)]
    # Separate runs, retain all results; no fastest-run selection.
    composition=[dict(rep=rep,**composition_evaluate(prefix,a.repetitions)) for rep in range(3) for prefix in (32,1000,10000)]
    for row in queries:print(json.dumps(dict(kind="singleton",**row),allow_nan=False),flush=True)
    for row in composition:print(json.dumps(dict(kind="composition",**row),allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="shared runner; exact old grouped methods at c97f8cf5 versus current, repeated staging tail diagnostic",singleton=queries,composition=composition),indent=2,allow_nan=False))
if __name__=="__main__":main()
