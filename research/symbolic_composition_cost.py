"""Public symbolic composition and builder comparison against exact staged paths."""
import argparse,json,random,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ketary as q
from ketary import _ergonomics
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from research.native_stage_profile import stats

def previous_apply(self,block,placements):
    from ketary._adapter import _append_bound_blocks
    if getattr(self,"_symbolic",False) and (self._qc.parameters or block._qc.parameters):
        # Isolate the native parameter table as well as the instruction
        # stream. Source stays unchanged, including self-application.
        candidate=self._qc.copy()
        changed=False
        for wires in placements:
            phase=candidate.global_phase
            candidate.compose(block._qc,qubits=list(wires),inplace=True)
            changed=changed or candidate.global_phase!=phase
        self._qc=candidate
    else:
        changed=_append_bound_blocks(self._qc,block._qc,placements)
    if changed:
        self._named_checkpoints={}
    return self



def previous_batch(c,append):
    if c.num_clbits or getattr(c,"_symbolic",False):
        candidate=c._qc.copy()
        append(candidate)
        c._qc=candidate
        return c
    start=len(c._qc.data);phase=c._qc.global_phase
    try:append(c._qc)
    except Exception:
        del c._qc.data[start:];c._qc.global_phase=phase;raise
    return c

def evaluate(n,count,seed=1101,reps=7):
    p,r=q.Circuit.parameter("p"),q.Circuit.parameter("r")
    block=q.Circuit.symbolic(2).ry(p,0).rz(p+r,1).cx(0,1).evolve(q.I(),time=r)
    rawblock=block.to_qiskit()
    def compose():
        c=q.Circuit.symbolic(n).ry(p,0)
        for i in range(count):c.apply(block,wires=[i%n,(i+1)%n])
        return c
    def build():
        c=q.Circuit.symbolic(n)
        for i in range(count):c.ry([p,r]*(n//2),range(n)).cx(pairs=q.chain(range(n)))
        return c
    expected=QuantumCircuit(n);expected.ry(p,0)
    for i in range(count):expected.compose(rawblock,qubits=[i%n,(i+1)%n],inplace=True)
    expected_build=QuantumCircuit(n)
    for i in range(count):
        for j in range(n):expected_build.ry((p,r)[j%2],j)
        expected_build.cx(list(range(n-1)),list(range(1,n)))
    routes={"compose":compose,"build":build};refs={"compose":expected,"build":expected_build}
    samples={k+"_"+mode:[] for k in routes for mode in ("old","new")};rnd=random.Random(seed)
    values={p:rnd.uniform(-.7,.7),r:rnd.uniform(-.7,.7)}
    for _ in range(reps):
        for k in rnd.sample(list(samples),len(samples)):
            route,mode=k.split("_")
            if mode=="old":
                obj,attr,fn=(q.Circuit,"_apply_placements",previous_apply) if route=="compose" else (_ergonomics,"_native_batch",previous_batch)
                with patch.object(obj,attr,fn):
                    t=time.perf_counter_ns();out=routes[route]();samples[k].append((time.perf_counter_ns()-t)/1e6)
            else:
                t=time.perf_counter_ns();out=routes[route]();samples[k].append((time.perf_counter_ns()-t)/1e6)
            assert out.to_qiskit()==refs[route]
            if n<=4:np.testing.assert_allclose(Operator(out.bind(values).to_qiskit()).data,Operator(refs[route].assign_parameters(values)).data,rtol=0,atol=1e-9)
    assert block.to_qiskit()==rawblock
    return dict(n=n,count=count,seed=seed,compose_gates=len(expected.data),build_gates=len(expected_build.data),stages={k:stats(v) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,12):
        for count in (4,16,64):
            row=evaluate(n,count,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="paired public construction and composition; strict native sequences and small operators; shared CI",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
