"""Paired product-stage diagnostics, pinned baseline pair function.

The baseline body is copied unchanged (apart from its name) from
ef2611291f96a3b7d20afcb814c9e8415ebf036f. Same native backend and output
semantics; shared CI is not controlled hardware evidence.
"""
import argparse,json,random,time
from collections.abc import Mapping
from itertools import islice
import numpy as np
import ketary as q
from ketary._ergonomics import _native_batch,_pairs
from ketary._validation import ResourceLimit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector
from research.circuit_rewrite_ladder import stats

def _baseline_pairs(c,name,a,b,pairs,*params):
    """Explicit ordered pair placement; no implicit zip or Cartesian mode."""
    if pairs is None:
        return getattr(c.gates,name)(*params,a,b)
    if a is not None or b is not None:
        raise ValueError("choose scalar wires or pairs, not both")
    if isinstance(pairs,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered wire pairs")
    gate=c.gates
    selected=[]
    try:
        for row in islice(iter(pairs),10001):
            # Exact immutable tuples need neither ABC dispatch nor iterator
            # materialization. Keep bounded consumption for every other row.
            if type(row) is tuple:
                pair=row
            else:
                if isinstance(row,(str,bytes,Mapping,set,frozenset)):
                    raise ValueError("expected ordered wire pair")
                pair=tuple(islice(iter(row),3))
            if len(pair)!=2:
                raise ValueError("each pair must contain two distinct wires")
            selected.append(gate._pair(*pair))
    except TypeError as exc:
        raise ValueError("expected ordered wire pairs") from exc
    if not selected:
        raise ValueError("expected at least one wire pair")
    if len(selected)>10000:
        raise ResourceLimit("pair batch supports at most 10000 pairs")
    # Only single-angle gates support aligned rows. Keep the established
    # native scalar broadcast unchanged, including symbolic parameters.
    if len(params)==1:
        theta=params[0]
        if isinstance(theta,(str,bytes,Mapping,set,frozenset)):
            raise ValueError("expected scalar angle or ordered angle sequence")
        try:
            angles=iter(theta)
        except TypeError:
            pass
        else:
            values=tuple(islice(angles,len(selected)+1))
            if len(values)!=len(selected):
                raise ValueError("angle and pair sequences must have equal length")
            values=tuple(c._gate_angle(v) for v in values)
            def append(native):
                method=getattr(native,name)
                for (first,second),angle in zip(selected,values,strict=True):
                    method(angle,first,second)
            return _native_batch(c,append)
    values=tuple(c._gate_angle(p) for p in params)
    first,second=zip(*selected,strict=True)
    return _native_batch(c,lambda native:getattr(native,name)(*values,list(first),list(second)))


def build_pairs(route,rows):
    if route=="qiskit":
        c=QuantumCircuit(4)
        a,b=zip(*rows,strict=True);c.cx(list(a),list(b));return c
    c=q.Circuit(4)
    (_baseline_pairs if route=="baseline" else _pairs)(c,"cx",None,None,rows)
    return c.to_qiskit()

def pair_profile(seed,reps):
    rng=random.Random(seed);rows=[]
    for count in (100,1000,10000):
        pairs=tuple(tuple(rng.sample(range(4),2)) for _ in range(count))
        expected=build_pairs("qiskit",pairs)
        for route in ("baseline","current"):
            assert build_pairs(route,pairs)==expected
            np.testing.assert_allclose(Operator(build_pairs(route,pairs[:32])).data,Operator(build_pairs("qiskit",pairs[:32])).data,atol=1e-9,rtol=0)
        times={k:[] for k in ("baseline","current","qiskit")}
        for _ in range(reps):
            for route in rng.sample(list(times),len(times)):
                start=time.perf_counter_ns();actual=build_pairs(route,pairs);end=time.perf_counter_ns()
                assert actual==expected
                times[route].append((end-start)/1e6)
        rows.append(dict(count=count,timings={k:stats(v) for k,v in times.items()},baseline_to_current_ratio=float(np.median(times["baseline"])/np.median(times["current"]))))
    return rows

def experiment(kind,seed):
    rng=np.random.default_rng(seed)
    p,r=q.Circuit.parameter_vector("a",2)
    placements=((3,0),(2,1))
    edges=((0,1,.8),(1,2,-.3),(2,3,1.1))
    h=q.Z(0)+.7*(q.Z(1)@q.Z(2))+.31*q.X(3)
    # Independently construct the native observable matrix using wire indexing.
    I=np.eye(2);Z=np.diag([1.,-1.]);X=np.array([[0.,1.],[1.,0.]])
    H=np.kron(np.eye(8),Z)+.7*np.kron(I,np.kron(Z,np.kron(Z,I)))+.31*np.kron(X,np.eye(8))
    def sdk():
        c=q.Circuit.symbolic(4)
        if kind=="qaoa":
            c.h(range(4))
            cost=sum((w*(q.Z(a)@q.Z(b)) for a,b,w in edges),q.I()*0)
            c.evolve(cost,time=p).rx(2*r,range(4))
        else:
            layer=q.Circuit.symbolic(2).ry(p,0).ry(r,1).cx(0,1)
            c.apply_each(layer,placements=placements)
            c.ry(p+r,range(4))
        return c
    def native():
        c=QuantumCircuit(4)
        if kind=="qaoa":
            c.h(range(4))
            for a,b,w in edges:c.rzz(2*w*p,a,b)
            c.rx(2*r,range(4))
        else:
            layer=QuantumCircuit(2);layer.ry(p,0);layer.ry(r,1);layer.cx(0,1)
            for wires in placements:c.compose(layer,qubits=wires,inplace=True)
            c.ry(p+r,range(4))
        return c
    start=time.perf_counter_ns();c=sdk();build=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();raw=native();native_build=(time.perf_counter_ns()-start)/1e6
    vals=tuple(tuple(map(float,row)) for row in rng.uniform(-.6,.6,(8,2)))
    before=c.to_qiskit()
    start=time.perf_counter_ns();plan=c.sweep_rows(vals);bind=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();refs=tuple(raw.assign_parameters(dict(zip((p,r),row,strict=True))) for row in vals);native_bind=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();results=plan.run();execute=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();native_results=tuple(Statevector.from_instruction(v) for v in refs);native_execute=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();got=tuple((v.math.expectation(h),v.math.observable_variance(h)) for v in results);read=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();expected=[]
    for v in native_results:
        x=v.data;hx=H@x;e=float(np.vdot(x,hx).real)
        expected.append((e,float(np.vdot(hx,hx).real-e*e)))
    native_read=(time.perf_counter_ns()-start)/1e6
    np.testing.assert_allclose(got,expected,atol=1e-9,rtol=0)
    for row,ref,result,(energy,variance) in zip(vals,refs,results,expected,strict=True):
        np.testing.assert_allclose(Operator(c.bind(dict(zip((p,r),row,strict=True))).to_qiskit()).data,Operator(ref).data,atol=1e-9,rtol=0)
        q.Contract(4,expectations={h:energy}).verify(result).require()
    assert c.to_qiskit()==before
    point=np.array(vals[0])
    def energy(row):
        v=Statevector.from_instruction(raw.assign_parameters(dict(zip((p,r),row,strict=True)))).data
        return float(np.vdot(v,H@v).real)
    eps=1e-5
    want=[(energy(point+eps*d)-energy(point-eps*d))/(2*eps) for d in np.eye(2)]
    gradient=c.expectation_jacobian(dict(zip((p,r),point,strict=True)),[h])
    np.testing.assert_allclose(gradient,[want],atol=1e-7,rtol=0)
    return dict(kind=kind,rows=8,width=4,seed=seed,stages_ms={"sdk":[build,bind,execute,read],"native":[native_build,native_bind,native_execute,native_read]},stage_order=["build","bind","execute","read"],result_payload_bytes=8*16*16,scope="authored matched states/energy/variance/gradient/contract; single stage timing diagnostic; not independent usability")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--seed",type=int,default=1101);p.add_argument("--reps",type=int,default=9);a=p.parse_args()
    print(json.dumps(dict(seed=a.seed,baseline="ef2611291f96a3b7d20afcb814c9e8415ebf036f",pair_profile=pair_profile(a.seed,a.reps),experiments=[experiment(k,a.seed) for k in ("vqe","qaoa")]),indent=2,allow_nan=False))
