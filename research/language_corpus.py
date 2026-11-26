"""LANG01–10 authored comparative corpus: ten parameterized tasks per family.

Each variant is executable, not generated-model output. Shared inputs and
imports are excluded consistently. This is not a human/agent usability study.
"""
import argparse,json,random,time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Operator,Statevector,SparsePauliOp,Pauli
from research.circuit_rewrite_ladder import metrics,stats

CASES=[
("LANG01","layers","operator",
"""layer=QuantumCircuit(2)
layer.ry(t,0)
layer.cx(0,1)
out=QuantumCircuit(4)
for pair in placements:out.compose(layer,qubits=pair,inplace=True)""",
"""layer=q.Circuit(2).ry(t,0).cx(0,1)
out=q.Circuit(4).apply_each(layer,placements=placements)""",None),
("LANG02","loops","operator",
"""block=QuantumCircuit(2)
block.h(0)
block.cx(0,1)
out=block.repeat(count)""",
"""out=q.bell().repeat(count)""",None),
("LANG03","basis","operator",
"""out=QuantumCircuit(len(label))
active=[i for i,b in enumerate(reversed(label)) if b=="1"]
if active:out.x(active)""",
"""out=q.Circuit(len(label))
active=[i for i,b in enumerate(reversed(label)) if b=="1"]
if active:out.x(active)""",
"""out=q.basis(label)"""),
("LANG04","observable","numeric",
"""H=SparsePauliOp.from_sparse_list([("Z",[0],t),("XX",[0,1],.8)],num_qubits=2)
c=QuantumCircuit(2)
c.h(0)
c.cx(0,1)
out=Statevector.from_instruction(c).expectation_value(H).real""",
"""H=t*q.Z(0)+.8*(q.X(0)@q.X(1))
out=q.bell().run().math.expectation(H)""",None),
("LANG05","shared_jacobian","numeric",
"""def f(a,b):
    c=QuantumCircuit(1)
    c.ry(a,0)
    c.ry(b,0)
    s=Statevector.from_instruction(c)
    return np.array([s.expectation_value(Pauli(k)).real for k in ("Z","X")])
d=(f(t+np.pi/2,2*t)-f(t-np.pi/2,2*t))/2
d+=f(t,2*t+np.pi/2)-f(t,2*t-np.pi/2)
out=d[:,None]""",
"""def f(a,b):
    return np.array(q.Circuit(1).ry(a,0).ry(b,0).run().math.expectations([q.Z(0),q.X(0)]))
d=(f(t+np.pi/2,2*t)-f(t-np.pi/2,2*t))/2
d+=f(t,2*t+np.pi/2)-f(t,2*t-np.pi/2)
out=d[:,None]""",
"""p=q.Circuit.parameter("t")
c=q.Circuit.symbolic(1).ry(p,0).ry(2*p,0)
out=c.expectation_jacobian({p:t},[q.Z(0),q.X(0)])"""),
("LANG06","symbolic_hamiltonian","operator",
"""p=Parameter("t")
c=QuantumCircuit(2)
c.h([0,1])
c.rzz(2*.8*p,0,1)
c.global_phase=-.5*p
out=c.assign_parameters({p:t})""",
"""p=q.Circuit.parameter("t")
H=.5*q.I()+.8*(q.Z(0)@q.Z(1))
out=q.Circuit.symbolic(2).h([0,1]).evolve(H,time=p).bind({p:t})""",None),
("LANG07","controlled_relative_phase","operator",
"""u=QuantumCircuit(1)
u.ry(t,0)
u.global_phase=.3
out=QuantumCircuit(2)
out.append(u.to_gate().control(1),[0,1])""",
"""out=q.Circuit(2).cry(t,0,1).p(.3,0)""",None),
("LANG08","verification","numeric",
"""c=QuantumCircuit(2)
c.h(0)
c.cx(0,1)
good=Statevector.from_instruction(c)
c.rz(t,0)
bad=Statevector.from_instruction(c)
out=tuple(all(np.isclose(r.expectation_value(Pauli(k)),1,rtol=0,atol=1e-9) for k in ("XX","ZZ")) for r in (good,bad))""",
"""c=q.bell()
contract=c.contract(expectations={q.X(0)@q.X(1):1,q.Z(0)@q.Z(1):1})
out=tuple(contract.verify(r).status=="PASS" for r in (c.run(),c.rz(t,0).run()))""",None),
("LANG09","ordered_shared_parameter","operator",
"""p=Parameter("t")
layer=QuantumCircuit(2)
layer.ry(p,0)
layer.cx(0,1)
c=QuantumCircuit(4)
for pair in placements:c.compose(layer,qubits=pair,inplace=True)
out=c.assign_parameters({p:t})""",
"""p=q.Circuit.parameter("t")
layer=q.Circuit.symbolic(2).ry(p,0).cx(0,1)
out=q.Circuit.symbolic(4).apply_each(layer,placements=placements).bind({p:t})""",None),
("LANG10","sweep","numeric",
"""p=Parameter("t")
c=QuantumCircuit(2)
c.ry(p,0)
c.cx(0,1)
out=tuple(Statevector.from_instruction(c.assign_parameters({p:v})).probabilities()[3] for v in values)""",
"""p=q.Circuit.parameter("t")
c=q.Circuit.symbolic(2).ry(p,0).cx(0,1)
out=tuple(r.math.probability("11") for r in c.sweep(t=values).run())""",None),
]
def evaluate(case,index,reps=3):
    lang,name,kind,native,current,candidate=case
    sources={"qiskit":native,"current":current,"candidate":candidate or current}
    rng=np.random.default_rng(1101+index);t=float(rng.uniform(.15,.85))
    placements=tuple(tuple(map(int,rng.choice(4,size=2,replace=False))) for _ in range(2+index%3))
    env=dict(q=q,np=np,QuantumCircuit=QuantumCircuit,Parameter=Parameter,Operator=Operator,
        Statevector=Statevector,SparsePauliOp=SparsePauliOp,Pauli=Pauli,t=t,
        count=1+index,label=format(index,"04b"),placements=placements,
        values=tuple(float(v) for v in rng.uniform(-.8,.8,4)))
    compiled={k:compile(s,"<trusted-language-fixture>","exec") for k,s in sources.items()}
    def execute(k):
        scope=dict(env);exec(compiled[k],scope);return scope["out"]
    def array(out):
        if kind=="operator":
            return Operator(out.to_qiskit() if isinstance(out,q.Circuit) else out).data
        return np.asarray(out)
    want=array(execute("qiskit"))
    if lang=="LANG05":np.testing.assert_allclose(want,[[-3*np.sin(3*t)],[3*np.cos(3*t)]],atol=1e-9,rtol=0)
    if lang=="LANG08":np.testing.assert_array_equal(want,[True,False])
    errors={};samples={k:[] for k in sources};rnd=random.Random(1101+index)
    for _ in range(reps):
        for k in rnd.sample(list(sources),len(sources)):
            start=time.perf_counter_ns();out=execute(k);samples[k].append((time.perf_counter_ns()-start)/1e6)
            got=array(out);np.testing.assert_allclose(got,want,atol=1e-9,rtol=0)
            errors[k]=float(np.max(np.abs(got.astype(complex)-want.astype(complex))))
    return dict(lang=lang,task=name,index=index,kind=kind,variants={k:dict(source=s,**metrics(s),time=stats(samples[k]),max_error=errors[k]) for k,s in sources.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    rows=[]
    for case in CASES:
        for index in range(10):
            row=evaluate(case,index);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="100 parameterized cases, ten authored task families; lexical metrics not independent human/agent evaluation; shared CI",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
