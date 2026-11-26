"""Paired public sweep binding study, including previous row dispatch."""
import argparse,json,random,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ketary as q
from qiskit.quantum_info import Operator
from ketary._ergonomics import SweepPlan
from research.native_stage_profile import stats

# Exact pre-PR public binding implementation, with absolute imports.
Circuit=q.Circuit
UnsupportedOperation=q.UnsupportedOperation
def previous_bind(self,bindings=None,**values):
    """Return an independent fully bound circuit; source is unchanged."""
    if self.num_clbits:
        raise UnsupportedOperation('symbolic classical binding is outside this subset')
    if bindings is not None and values:
        raise ValueError("choose a parameter mapping or named values")
    if bindings is None:
        params={p.name:p for p in self.parameters}
        if len(params)!=len(self.parameters) or set(values)!=set(params):
            raise ValueError("named binding must cover each unique parameter")
        bindings={params[name]:value for name,value in values.items()}
    else:
        from collections.abc import Mapping
        from itertools import islice
        if not isinstance(bindings,Mapping):
            if isinstance(bindings,(str,bytes,set,frozenset)):
                raise TypeError("expected mapping or ordered numeric values")
            params=self.parameters
            try:
                vals=tuple(islice(iter(bindings),len(params)+1))
            except TypeError as exc:
                raise TypeError("expected mapping or ordered numeric values") from exc
            if len(vals)!=len(params):
                raise ValueError("ordered binding must cover exactly the native parameter order")
            bindings=dict(zip(params,vals,strict=True))
    # Only internal circuits have the validated structure invariant.
    # Native assignment preserves it; check evaluated numeric values,
    # including expression overflow, without rechecking every gate kind.
    from ketary._adapter import _validate_bound_values
    from ketary._validation import _angle
    if set(bindings)!=set(self._qc.parameters):
        raise ValueError("bindings must cover exactly the template parameters")
    numeric={key:_angle(value) for key,value in bindings.items()}
    try:
        bound=self._qc.assign_parameters(numeric,inplace=False,flat_input=True)
    except (ZeroDivisionError,OverflowError) as exc:
        raise ValueError("parameter expression must evaluate to a finite real number") from exc
    _validate_bound_values(bound)
    c=Circuit.__new__(Circuit)
    c._qc=bound
    return c


def previous(self,circuit,rows,params):
    self._payloads=tuple(previous_bind(circuit,{params[name]:v for name,v in row}) for row in rows)
    self._rows=rows
    self._width=circuit.num_qubits

def evaluate(n,layers,count,seed=1101,reps=7):
    rng=np.random.default_rng(seed);p=q.Circuit.parameter_vector("p",n)
    c=q.Circuit.symbolic(n)
    for k in range(layers):
        c.ry([v*(k+1)/layers for v in p],range(n)).cx(pairs=q.chain(range(n)))
    c.evolve(q.I(),time=p[0])
    raw=c.to_qiskit();params=c.parameters
    rows=tuple(tuple(float(v) for v in row) for row in rng.uniform(-.8,.8,(count,n)))
    named={key.name:tuple(row[i] for row in rows) for i,key in enumerate(params)}
    expected=tuple(raw.assign_parameters(dict(zip(params,row,strict=True)),inplace=False,flat_input=True) for row in rows)
    def verify(plan):
        assert len(plan._payloads)==count
        for payload,native in zip(plan._payloads,expected,strict=True):
            assert payload.to_qiskit()==native
        if n<=4:
            np.testing.assert_allclose(Operator(plan._payloads[-1].to_qiskit()).data,Operator(expected[-1]).data,rtol=0,atol=1e-9)
    routes={"named":lambda:c.sweep(**named),"ordered":lambda:c.sweep_rows(rows)}
    for fn in routes.values():verify(fn())
    with patch.object(SweepPlan,"_initialize_rows",previous):
        for fn in routes.values():verify(fn())
    samples={k+"_"+mode:[] for k in routes for mode in ("old","new")}
    samples.update({k:[] for k in ("public_identity","public_name","public_order","previous_identity","previous_name","previous_order","native_assignment")})
    row=rows[0];mapping=dict(zip(params,row,strict=True));named_row={k.name:v for k,v in mapping.items()}
    others={"public_identity":lambda:c.bind(mapping),"public_name":lambda:c.bind(**named_row),"public_order":lambda:c.bind(row),"previous_identity":lambda:previous_bind(c,mapping),"previous_name":lambda:previous_bind(c,**named_row),"previous_order":lambda:previous_bind(c,row),"native_assignment":lambda:raw.assign_parameters(mapping,inplace=False,flat_input=True)}
    rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(samples),len(samples)):
            if k in others:
                t=time.perf_counter_ns();out=others[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
                assert (out if k=="native_assignment" else out.to_qiskit())==expected[0]
            else:
                route,mode=k.split("_")
                if mode=="old":
                    with patch.object(SweepPlan,"_initialize_rows",previous):
                        t=time.perf_counter_ns();out=routes[route]();samples[k].append((time.perf_counter_ns()-t)/1e6)
                else:
                    t=time.perf_counter_ns();out=routes[route]();samples[k].append((time.perf_counter_ns()-t)/1e6)
                assert all(p.to_qiskit()==v for p,v in zip(out._payloads,expected,strict=True))
    assert c.to_qiskit()==raw
    return dict(n=n,layers=layers,gates=len(raw.data),rows=count,seed=seed,stages={k:stats(v) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (2,4,8):
        for layers in (1,4,8):
            for count in (1,8,32):
                row=evaluate(n,layers,count,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="paired public sweep plan construction; previous public bind and sweep dispatch reproduced; no execution timing; shared CI",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
