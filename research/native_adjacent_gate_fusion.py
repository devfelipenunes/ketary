"""Issue #304: adjacent native rotation/involution ablation.

Research only: no new IR, no transpiler or SDK dispatch.
"""
import argparse,json,math,random,statistics,time
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit,transpile
from qiskit.circuit import Parameter
from qiskit.quantum_info import Operator,Statevector

ROTATIONS={"rx","ry","rz","p","rxx","ryy","rzz"}
INVOLUTIONS={"h","x","y","z","cx","cz","swap"}

def fuse(raw):
    if type(raw) is not QuantumCircuit or raw.num_clbits or raw.metadata or raw.layout is not None:
        raise ValueError("plain unitary research input required")
    if not 1<=raw.num_qubits<=8 or len(raw.data)>10000:
        raise ValueError("bounded research fixture required")
    out=raw.copy_empty_like()
    out.global_phase=raw.global_phase
    # Use the actual native circuit's last instruction, not a second IR.
    for item in raw.data:
        name=item.operation.name
        wires=tuple(raw.find_bit(w).index for w in item.qubits)
        if name not in ROTATIONS|INVOLUTIONS or item.clbits:
            raise ValueError("unsupported research instruction")
        if out.data:
            last=out.data[-1]
            same=name==last.operation.name and wires==tuple(out.find_bit(w).index for w in last.qubits)
            if same and name in INVOLUTIONS:
                out.data.pop()
                continue
            if same and name in ROTATIONS:
                a,b=last.operation.params[0],item.operation.params[0]
                # Preserve explicit symbolic identities; restrict numeric
                # addition to a moderate magnitude to avoid phase reduction.
                if getattr(a,"parameters",()) or getattr(b,"parameters",()):
                    combined=a+b
                elif all(math.isfinite(float(x)) and abs(float(x))<=1e4 for x in (a,b,float(a)+float(b))):
                    combined=float(a)+float(b)
                else:
                    combined=None
                if combined is not None:
                    # A symbolic cancellation can remove a parameter. Keep
                    # the original pair unless its exact identity set survives.
                    identities=set(getattr(a,"parameters",()))|set(getattr(b,"parameters",()))
                    if set(getattr(combined,"parameters",()))==identities:
                        out.data.pop()
                        getattr(out,name)(combined,*wires)
                        continue
        out.append(item.operation,list(wires))
    # Never turn global phase into an omitted or modulo-2pi spin angle.
    return out

def fixture(n,layers,symbolic):
    if n not in (3,6,8) or layers not in (8,64):raise ValueError("bounded workload")
    raw=QuantumCircuit(n,global_phase=.37)
    t=Parameter("t");p=Parameter("p")
    for k in range(layers):
        w=k%n;z=(w+1)%n
        a=t if symbolic else .11
        b=p if symbolic else -.23
        raw.rx(a,w);raw.rx(b,w)
        raw.rzz(a,w,z);raw.rzz(b,w,z)
        raw.x(z);raw.x(z)
        raw.cx(w,z);raw.cx(w,z)
        raw.rz(.17,z)
    return raw

def evaluate(n,layers,symbolic,reps):
    if not 3<=reps<=30:raise ValueError("bounded repetitions")
    raw=fixture(n,layers,symbolic);candidate=fuse(raw)
    assert set(raw.parameters)==set(candidate.parameters)
    rng=np.random.default_rng(304+n+layers)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    bindings={p:.17+.13*i for i,p in enumerate(raw.parameters)}
    a=raw.assign_parameters(bindings);b=candidate.assign_parameters(bindings)
    common=[transpile(x,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=304) for x in (a,b)]
    expected=Operator(a).data
    for x in (b,*common):
        np.testing.assert_allclose(Operator(x).data,expected,atol=1e-9,rtol=0)
    routes={"fusion":lambda:fuse(raw),"original_run":lambda:Statevector(v).evolve(a),
            "fused_run":lambda:Statevector(v).evolve(b),"original_common_run":lambda:Statevector(v).evolve(common[0]),
            "fused_common_run":lambda:Statevector(v).evolve(common[1])}
    samples={k:[] for k in routes};orders=[];rnd=random.Random(n+layers)
    for _ in range(reps):
        order=list(routes);rnd.shuffle(order);orders.append(order)
        for name in order:
            t=time.perf_counter_ns();out=routes[name]();samples[name].append((time.perf_counter_ns()-t)/1e6)
            if name!="fusion":np.testing.assert_allclose(out.data,expected@v,atol=1e-9,rtol=0)
    return dict(n=n,layers=layers,symbolic=symbolic,source_gates=len(raw.data),fused_gates=len(candidate.data),
                common_source_gates=len(common[0].data),common_fused_gates=len(common[1].data),orders=orders,
                operator_error=float(np.max(np.abs(Operator(b).data-expected))),
                retained_state_bytes=v.nbytes,
                variants={k:dict(raw_ms=x,p50_ms=statistics.median(x),p95_ms=float(np.quantile(x,.95))) for k,x in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=7)
    a=p.parse_args();rows=[]
    for n in (3,6,8):
        for layers in (8,64):
            for symbolic in (False,True):
                row=evaluate(n,layers,symbolic,a.repetitions);rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="adjacent exact native research, no runtime promotion; state payload and instruction counts not RSS",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
