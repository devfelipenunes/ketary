"""Authored matched snippets for abstraction research; not independent usability.

Static source strings below are local, reviewed fixtures only, never user input.
Run: python -m research.abstraction_atlas --output atlas.json --repetitions 7
"""
import argparse
import ast
import io
import json
import platform
import random
import statistics
import time
import tokenize
from importlib.metadata import version
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate, PauliEvolutionGate, StatePreparation
from qiskit.quantum_info import Operator, Statevector, SparsePauliOp
from research import abstraction_primitives as p

# Explicit matched source, not a generated expansion counted as authored code.
# Native library constructors included where their semantics match the task.
CASES=[
("bell","states","c=q.bell()","c=q.bell()","c=QuantumCircuit(2); c.h(0); c.cx(0,1)"),
("ghz","states","c=q.ghz(4)","c=q.ghz(4)","c=QuantumCircuit(4); c.h(0); c.cx([0,1,2],[1,2,3])"),
("graph_ring","topology","c=q.Circuit(4).h(range(4)).cz(pairs=q.ring(range(4)))","c=p.graph_state(4,q.ring(range(4)))","c=QuantumCircuit(4); c.h(range(4)); c.cz([0,1,2,3],[1,2,3,0])"),
("graph_star","topology","c=q.Circuit(4).h(range(4)).cz(pairs=q.star(range(4)))","c=p.graph_state(4,q.star(range(4)))","c=QuantumCircuit(4); c.h(range(4)); c.cz(0,[1,2,3])"),
("aligned_cp","fourier","c=q.Circuit(4)\nfor a,(i,j) in zip(angles,pairs): c.cp(a,i,j)","c=p.aligned(q.Circuit(4),'cp',angles,pairs)","c=QuantumCircuit(4)\nfor a,(i,j) in zip(angles,pairs): c.cp(a,i,j)"),
("aligned_rzz","ising","c=q.Circuit(4)\nfor a,(i,j) in zip(angles,pairs): c.rzz(a,i,j)","c=p.aligned(q.Circuit(4),'rzz',angles,pairs)","c=QuantumCircuit(4)\nfor a,(i,j) in zip(angles,pairs): c.rzz(a,i,j)"),
("aligned_crx","variational","c=q.Circuit(4)\nfor a,(i,j) in zip(angles,pairs): c.crx(a,i,j)","c=p.aligned(q.Circuit(4),'crx',angles,pairs)","c=QuantumCircuit(4)\nfor a,(i,j) in zip(angles,pairs): c.crx(a,i,j)"),
("qft4","fourier","c=q.qft(4)","c=q.qft(4)","c=QuantumCircuit(4); c.append(QFTGate(4),range(4))"),
("qpe_phase","phase_estimation","c=q.phase_estimation(.375,precision=3)","u=q.Circuit(1).p(.75*np.pi,0); c=q.Circuit(4).x(3).h(range(3))\nfor i in range(3): c.apply(p.controlled(p.power(u,2**i)),wires=[i,3])\nc.apply(q.qft(3,inverse=True),wires=range(3))","c=QuantumCircuit(4); c.x(3); c.h(range(3))\nfor i in range(3): c.cp(.75*np.pi*2**i,i,3)\nc.append(QFTGate(3).inverse(),range(3))"),
("parity","oracle","c=q.Circuit(4).cx(pairs=[(0,3),(2,3)])","c=p.parity(4,[0,2],3)","c=QuantumCircuit(4); c.cx([0,2],3)"),
("bv_oracle","oracle","c=q.parity_oracle('101')","c=p.parity(4,[0,2],3)","c=QuantumCircuit(4); c.cx([0,2],3)"),
("basis","preparation","c=q.Circuit(4).x([0,2])","c=p.basis('0101')","c=QuantumCircuit(4); c.x([0,2])"),
("increment3","arithmetic","c=q.Circuit(3).ccx(0,1,2).cx(0,1).x(0)","c=p.increment(3)","c=QuantumCircuit(3); c.ccx(0,1,2); c.cx(0,1); c.x(0)"),
("increment4","arithmetic","c=q.Circuit(4).mcx([0,1,2],3).ccx(0,1,2).cx(0,1).x(0)","c=p.increment(4)","c=QuantumCircuit(4); c.mcx([0,1,2],3); c.ccx(0,1,2); c.cx(0,1); c.x(0)"),
("repeat","composition","c=q.bell().repeat(3)","c=p.power(q.bell(),3)","u=QuantumCircuit(2); u.h(0); u.cx(0,1); c=u.repeat(3)"),
("adjoint","composition","c=q.bell().inverse()","c=p.power(q.bell(),-1)","u=QuantumCircuit(2); u.h(0); u.cx(0,1); c=u.inverse()"),
("tensor","composition","c=q.Circuit(3).apply(q.bell(),wires=[0,1]).ry(.3,2)","c=p.tensor(q.bell(),q.Circuit(1).ry(.3,0))","a=QuantumCircuit(2); a.h(0); a.cx(0,1); b=QuantumCircuit(1); b.ry(.3,0); c=b.tensor(a)"),
("conjugation","reversible","c=q.Circuit(2).compute_action_uncompute(q.Circuit(2).cx(0,1),q.Circuit(1).z(0),compute_wires=[0,1],action_wires=[1])","c=p.conjugate(q.Circuit(2).cx(0,1),q.Circuit(1).z(0),n=2,compute_wires=[0,1],action_wires=[1])","c=QuantumCircuit(2); c.cx(0,1); c.z(1); c.cx(0,1)"),
("reflection","search","c=q.Circuit(1).h(0).z(0).h(0)","c=p.reflection(q.Circuit(1).h(0))","c=QuantumCircuit(1); c.x(0)"),
("pauli_xz","simulation","c=q.Circuit(2).h(0).cx(0,1).rz(.6,1).cx(0,1).h(0)","c=p.pauli_rotation('ZX',.6)","c=QuantumCircuit(2); c.append(PauliEvolutionGate(SparsePauliOp('ZX'),time=.3),range(2))"),
("ising","simulation","c=q.Circuit(3).rzz(.6,0,1).rzz(-.24,1,2)","c=p.evolve(q.Z(0)@q.Z(1)-.4*(q.Z(1)@q.Z(2)),.3)","c=QuantumCircuit(3); c.append(PauliEvolutionGate(SparsePauliOp.from_list([('IZZ',1),('ZZI',-.4)]),time=.3),range(3))"),
("mixer","qaoa","c=q.Circuit(3).rx(.6,range(3))","c=p.evolve(sum(q.X(i) for i in range(3)),.3,n=3)","c=QuantumCircuit(3); c.rx(.6,range(3))"),
("qaoa_layer","qaoa","c=q.Circuit(3).h(range(3)).rzz(.6,pairs=[(0,1),(1,2)]).rx(.4,range(3))","c=q.Circuit(3).h(range(3)).apply(p.evolve(q.Z(0)@q.Z(1)+q.Z(1)@q.Z(2),.3)).apply(p.evolve(sum(q.X(i) for i in range(3)),.2))","c=QuantumCircuit(3); c.h(range(3)); c.rzz(.6,0,1); c.rzz(.6,1,2); c.rx(.4,range(3))"),
("vqe_layers","variational","c=q.Circuit(2)\nfor row in rows: c.ry(row,[0,1]).cx(0,1)","t=q.Circuit.parameter_vector('t',2); u=q.Circuit.symbolic(2).ry(t,[0,1]).cx(0,1); c=p.layers(u,rows)","c=QuantumCircuit(2)\nfor row in rows: c.ry(row[0],0); c.ry(row[1],1); c.cx(0,1)"),
("walk_step","walk","c=q.Circuit(2).h(0).cx(0,1).repeat(4)","c=p.power(q.Circuit(2).h(0).cx(0,1),4)","u=QuantumCircuit(2); u.h(0); u.cx(0,1); c=u.repeat(4)"),
("controlled_phase","phase_estimation","c=q.Circuit(2).cp(.37,0,1)","c=p.controlled(q.Circuit(1).p(.37,0))","c=QuantumCircuit(2); c.cp(.37,0,1)"),
("trotter_lie","simulation","c=q.Circuit(1)\nfor _ in range(4): c.rx(.2,0).rz(.14,0)","c=p.product_formula(q.X(0)+.7*q.Z(0),.4,steps=4)","c=QuantumCircuit(1)\nfor _ in range(4): c.rx(.2,0); c.rz(.14,0)"),
]

def metrics(source):
    tree=ast.parse(source)
    return {"tokens":sum(t.type not in (tokenize.ENCODING,tokenize.ENDMARKER,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT) for t in tokenize.generate_tokens(io.StringIO(source).readline)),
            "ast_nodes":sum(1 for _ in ast.walk(tree)),
            "loops":sum(isinstance(x,(ast.For,ast.While,ast.comprehension)) for x in ast.walk(tree)),
            "calls":sum(isinstance(x,ast.Call) for x in ast.walk(tree)),
            "numeric_literals":sum(isinstance(x,ast.Constant) and type(x.value) in (int,float) for x in ast.walk(tree))}
def fixture(source):
    code=compile(source,"<authored-fixture>","exec")
    def build():
        env={"q":q,"p":p,"np":np,"QuantumCircuit":QuantumCircuit,"QFTGate":QFTGate,
             "PauliEvolutionGate":PauliEvolutionGate,"SparsePauliOp":SparsePauliOp,
             "angles":[.2,-.31,.75],"pairs":[(2,0),(1,3),(0,3)],"rows":[[.1,.2],[.3,.4]]}
        exec(code,env)
        return env["c"]
    return build
def native(c):
    return c.to_qiskit() if isinstance(c,q.Circuit) else c
def state(c,v):
    return c.run(initial_state=v).math.statevector() if isinstance(c,q.Circuit) else Statevector(v).evolve(c).data.copy()
def stats(xs):
    return {"raw_ms":xs,"median_ms":statistics.median(xs),"p95_ms":float(np.quantile(xs,.95))}
def evaluate(case,repetitions=7,seed=1101):
    name,family,*sources=case
    keys=("current","candidate","qiskit")
    builds=dict(zip(keys,map(fixture,sources),strict=True))
    circuits={k:fn() for k,fn in builds.items()}
    reference=Operator(native(circuits["qiskit"])).data
    rng=np.random.default_rng(seed);v=rng.normal(size=reference.shape[0])+1j*rng.normal(size=reference.shape[0]);v/=np.linalg.norm(v)
    expected=reference@v
    result={}
    for k,s in zip(keys,sources,strict=True):
        c=circuits[k];raw=native(c)
        error=float(np.max(np.abs(Operator(raw).data-reference)))
        se=float(np.max(np.abs(state(c,v)-expected)))
        if max(error,se)>1e-9:raise AssertionError(f"{name}/{k}: strict operator {error}, state {se}")
        result[k]={"source":s,**metrics(s),"logical_instructions":len(raw.data),"logical_depth":raw.depth(),
                   "operator_error":error,"state_error":se,"construction_ms":[],"execution_ms":[]}
    rand=random.Random(seed)
    for _ in range(repetitions):
        order=list(keys);rand.shuffle(order)
        for k in order:
            start=time.perf_counter_ns();c=builds[k]();elapsed=time.perf_counter_ns()-start
            result[k]["construction_ms"].append(elapsed/1e6)
            start=time.perf_counter_ns();state(c,v);elapsed=time.perf_counter_ns()-start
            result[k]["execution_ms"].append(elapsed/1e6)
    for row in result.values():
        for metric in ("construction_ms","execution_ms"):row[metric]=stats(row[metric])
    return {"name":name,"family":family,"variants":result}

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True);parser.add_argument("--repetitions",type=int,default=7);parser.add_argument("--seed",type=int,default=1101);a=parser.parse_args()
    if not 3<=a.repetitions<=30:parser.error("3..30 repetitions")
    rows=[]
    for case in CASES:
        row=evaluate(case,a.repetitions,a.seed);rows.append(row)
        print(json.dumps({"name":row["name"],"variants":{k:{m:v[m] for m in ("tokens","loops","calls","logical_instructions","operator_error","state_error","construction_ms","execution_ms")} for k,v in row["variants"].items()}}),flush=True)
    a.output.write_text(json.dumps({"scope":"authored matched unitary tasks; shared CI diagnostic; no human/agent evidence","seed":a.seed,"repetitions":a.repetitions,"python":platform.python_version(),"qiskit":version("qiskit"),"ketary":version("ketary"),"rows":rows},indent=2,allow_nan=False))
if __name__=="__main__":main()
