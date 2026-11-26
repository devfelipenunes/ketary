"""RF04–06: executable authored Ketary rewrite ladder, not a usability study.

L0 scalar gates; L1 fluent/batched; L2 mathematical/reusable pattern when it
actually helps. Qiskit has its own idiomatic baseline. All code is static,
reviewed fixture source, not user-supplied code. Shared inputs are excluded
consistently and printed with results. Preserve every negative result.
"""
import argparse,ast,io,json,platform,random,statistics,time,tokenize
from collections import Counter
from pathlib import Path
from importlib.metadata import version
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import QFTGate,PauliEvolutionGate
from qiskit.quantum_info import Operator,Statevector,SparsePauliOp

# Different stages are actual complete circuit builders, not token-only
# edits. Include a native library baseline where it matches the intent.
CASES=[
("bell","c=q.Circuit(2); c.h(0); c.cx(0,1)","c=q.Circuit(2).h(0).cx(0,1)","c=q.bell()","c=QuantumCircuit(2); c.h(0); c.cx(0,1)","Factory communicates the named state."),
("ghz","c=q.Circuit(n); c.h(0)\nfor i in range(n-1): c.cx(i,i+1)","c=q.Circuit(n).h(0).cx(pairs=q.chain(range(n)))","c=q.ghz(n)","c=QuantumCircuit(n); c.h(0); c.cx(list(range(n-1)),list(range(1,n)))","Chain expresses topology; GHZ expresses state."),
("ring","c=q.Circuit(n)\nfor i in range(n): c.h(i)\nfor i in range(n): c.cz(i,(i+1)%n)","c=q.Circuit(n).h(range(n)).cz(pairs=q.ring(range(n)))","c=q.Circuit(n).h(range(n)).cz(pairs=q.ring(range(n)))","c=QuantumCircuit(n); c.h(range(n)); c.cz(list(range(n)),list(range(1,n))+[0])","Stop: no extra topology synonym needed."),
("cp_row","c=q.Circuit(n)\nfor theta,(a,b) in zip(angles,edges): c.cp(theta,a,b)","c=q.Circuit(n).cp(angles,pairs=edges)","c=q.Circuit(n).cp(angles,pairs=edges)","c=QuantumCircuit(n)\nfor theta,(a,b) in zip(angles,edges): c.cp(theta,a,b)","Aligned angles remove manual pairing, preserve order."),
("weighted_ising","c=q.Circuit(n)\nfor w,(a,b) in zip(weights,edges): c.rzz(2*gamma*w,a,b)","c=q.Circuit(n).rzz([2*gamma*w for w in weights],pairs=edges)","c=q.Circuit(n).rzz([2*gamma*w for w in weights],pairs=edges)","c=QuantumCircuit(n)\nfor w,(a,b) in zip(weights,edges): c.rzz(2*gamma*w,a,b)","Stop at aligned native gates until evolve is justified."),
("qft","c=q.Circuit(n)\nfor t in reversed(range(n)):\n c.h(t)\n for k in reversed(range(t)): c.cp(np.pi/2**(t-k),k,t)\nfor i in range(n//2): c.swap(i,n-1-i)","c=q.Circuit(n)\nfor t in reversed(range(n)):\n c.h(t)\n if t: c.cp([np.pi/2**(t-k) for k in reversed(range(t))],pairs=[(k,t) for k in reversed(range(t))])\nc.swap(pairs=[(i,n-1-i) for i in range(n//2)])","c=q.qft(n)","c=QuantumCircuit(n); c.append(QFTGate(n),range(n))","Named algorithm beats generic mechanics; middle rewrite may be longer."),
("qaoa","c=q.Circuit(n)\nfor i in range(n): c.h(i)\nfor g,beta in schedule:\n for w,(a,b) in zip(weights,edges): c.rzz(2*g*w,a,b)\n for i in range(n): c.rx(2*beta,i)","c=q.Circuit(n).h(range(n))\nfor g,beta in schedule: c.rzz([2*g*w for w in weights],pairs=edges).rx(2*beta,range(n))","c=q.Circuit(n).h(range(n))\nfor g,beta in schedule: c.rzz([2*g*w for w in weights],pairs=edges).rx(2*beta,range(n))","c=QuantumCircuit(n); c.h(range(n))\nfor g,beta in schedule:\n for w,(a,b) in zip(weights,edges): c.rzz(2*g*w,a,b)\n c.rx(2*beta,range(n))","Keep the algorithmic loop; remove only gate placement loops."),
("vqe","c=q.Circuit(n)\nfor row in rows:\n for i,t in enumerate(row): c.ry(t,i)\n for i in range(n-1): c.cx(i,i+1)","c=q.Circuit(n)\nfor row in rows: c.ry(row,range(n)).cx(pairs=q.chain(range(n)))","c=q.Circuit(n)\nfor row in rows: c.ry(row,range(n)).cx(pairs=q.chain(range(n)))","c=QuantumCircuit(n)\nfor row in rows:\n for i,t in enumerate(row): c.ry(t,i)\n c.cx(list(range(n-1)),list(range(1,n)))","No need for an extra layer type."),
("repeat","c=q.Circuit(2)\nfor i in range(5): c.h(0); c.cx(0,1)","c=q.Circuit(2)\nfor i in range(5): c.apply(q.bell())","c=q.bell().repeat(5)","u=QuantumCircuit(2); u.h(0); u.cx(0,1); c=u.repeat(5)","Reuse block; repeated construction is eliminated."),
("bv","c=q.Circuit(4).x(3).h(range(4))\nfor i,b in enumerate(reversed(mask)):\n if b=='1': c.cx(i,3)\nc.h(range(3))","c=q.deutsch_jozsa(q.parity_oracle(mask))","c=q.bernstein_vazirani(mask)","c=QuantumCircuit(4); c.x(3); c.h(range(4))\nfor i,b in enumerate(reversed(mask)):\n if b=='1': c.cx(i,3)\nc.h(range(3))","Express oracle promise via existing factory."),
("basis","c=q.Circuit(n)\nfor i,b in enumerate(reversed(label)):\n if b=='1': c.x(i)","c=q.Circuit(n).x([i for i,b in enumerate(reversed(label)) if b=='1'])","c=q.Circuit(n).x([i for i,b in enumerate(reversed(label)) if b=='1'])","c=QuantumCircuit(n); c.x([i for i,b in enumerate(reversed(label)) if b=='1'])","Factory remains candidate; keep current code if it is adequate."),
("conjugation","c=q.Circuit(2); c.cx(0,1); c.z(1); c.cx(0,1)","c=q.Circuit(2).cx(0,1).z(1).cx(0,1)","c=q.Circuit(2).compute_action_uncompute(q.Circuit(2).cx(0,1),q.Circuit(1).z(0),compute_wires=[0,1],action_wires=[1])","c=QuantumCircuit(2); c.cx(0,1); c.z(1); c.cx(0,1)","Named pattern may be verbose: retain the shorter explicit circuit."),
("qpe","c=q.Circuit(4).x(3).h(range(3))\nfor i in range(3): c.cp(2*np.pi*phase*2**i,i,3)\nc.apply(q.qft(3,inverse=True),wires=range(3))","c=q.Circuit(4).x(3).h(range(3)).cp([2*np.pi*phase*2**i for i in range(3)],pairs=[(i,3) for i in range(3)]).apply(q.qft(3,inverse=True),wires=range(3))","c=q.phase_estimation(phase,precision=3)","c=QuantumCircuit(4); c.x(3); c.h(range(3))\nfor i in range(3): c.cp(2*np.pi*phase*2**i,i,3)\nc.append(QFTGate(3).inverse(),range(3))","Use existing QPE factory for its documented special case."),
]
KEYS=("scalar","fluent","intent","qiskit")
def env():
    return dict(q=q,np=np,QuantumCircuit=QuantumCircuit,QFTGate=QFTGate,n=4,
                angles=[.2,-.31,.75],edges=[(2,0),(1,3),(0,3)],weights=[.5,-.4,.9],
                gamma=.3,schedule=[(.3,.2),(.7,-.1)],rows=[[.1,.2,.3,.4],[.5,-.2,.7,.8]],
                mask="101",label="0101",phase=.375)
def metrics(source):
    tree=ast.parse(source);nodes=list(ast.walk(tree))
    tokens=sum(t.type not in (tokenize.ENCODING,tokenize.ENDMARKER,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT) for t in tokenize.generate_tokens(io.StringIO(source).readline))
    def nested(node,depth=0):
        d=depth+int(isinstance(node,(ast.For,ast.While,ast.If,ast.comprehension)))
        return max([d]+[nested(x,d) for x in ast.iter_child_nodes(node)])
    calls=[x.func.attr for x in nodes if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]
    # Count repeated nontrivial expression/statement shapes, not trivial names
    # or constants. This is exact syntactic duplication, not semantics.
    duplicates=Counter(ast.dump(x,include_attributes=False) for x in nodes
                       if isinstance(x,(ast.expr,ast.stmt)) and sum(1 for _ in ast.walk(x))>=5)
    return dict(duplicate_ast_groups=sum(v>1 for v in duplicates.values()),
                duplicate_ast_excess=sum(v-1 for v in duplicates.values() if v>1),
                tokens=tokens,ast_nodes=len(nodes),statements=sum(isinstance(x,ast.stmt) for x in nodes),
                loops=sum(isinstance(x,(ast.For,ast.While,ast.comprehension)) for x in nodes),
                branches=sum(isinstance(x,ast.If) for x in nodes),nesting=nested(tree),calls=sum(isinstance(x,ast.Call) for x in nodes),
                numeric_literals=sum(isinstance(x,ast.Constant) and type(x.value) in (int,float) for x in nodes),
                attribute_call_vocabulary=sorted(set(calls)))
def builder(source):
    code=compile(source,"<reviewed-rewrite>","exec")
    def build():
        scope=env();exec(code,scope);return scope["c"]
    return build
def native(c):return c.to_qiskit() if isinstance(c,q.Circuit) else c
def state(c,v):return c.run(initial_state=v).math.statevector() if isinstance(c,q.Circuit) else Statevector(v).evolve(c).data.copy()
def stats(values):return dict(raw_ms=values,p50_ms=statistics.median(values),p95_ms=float(np.quantile(values,.95)))
def evaluate(case,seed=1101,reps=7):
    name,*rest=case;sources=rest[:4];rationale=rest[-1]
    builds=dict(zip(KEYS,map(builder,sources),strict=True));circuits={k:b() for k,b in builds.items()}
    ref=Operator(native(circuits["qiskit"])).data
    rng=np.random.default_rng(seed);v=rng.normal(size=len(ref))+1j*rng.normal(size=len(ref));v/=np.linalg.norm(v)
    result={}
    for k,source in zip(KEYS,sources,strict=True):
        c=circuits[k];raw=native(c);expanded=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
        err=max(float(np.max(np.abs(Operator(raw).data-ref))),float(np.max(np.abs(Operator(expanded).data-ref))),float(np.max(np.abs(state(c,v)-ref@v))))
        if err>1e-9:raise AssertionError(f"{name}/{k} semantic regression {err}")
        result[k]=dict(source=source,**metrics(source),logical_gates=len(raw.data),logical_depth=raw.depth(),basis_gates=len(expanded.data),basis_depth=expanded.depth(),max_error=err,build=[],run=[])
    # Warmup each path; interleaved deterministic random order.
    for b in builds.values():state(b(),v)
    order_rng=random.Random(seed)
    for _ in range(reps):
        order=list(KEYS);order_rng.shuffle(order)
        for k in order:
            t=time.perf_counter_ns();c=builds[k]();result[k]["build"].append((time.perf_counter_ns()-t)/1e6)
            t=time.perf_counter_ns();state(c,v);result[k]["run"].append((time.perf_counter_ns()-t)/1e6)
    for row in result.values():
        for k in ("build","run"):row[k]=stats(row[k])
    best=min(KEYS[:3],key=lambda k:(result[k]["tokens"],KEYS.index(k)))
    return dict(name=name,rationale=rationale,shortest_ketary=best,variants=result)
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True);parser.add_argument("--seed",type=int,default=1101);parser.add_argument("--reps",type=int,default=7);a=parser.parse_args()
    if not 3<=a.reps<=30:parser.error("3..30 repetitions")
    rows=[]
    for case in CASES:
        row=evaluate(case,a.seed,a.reps);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="authored source rewrite; not human readability or independent evaluation",seed=a.seed,python=platform.python_version(),qiskit=version("qiskit"),ketary=version("ketary"),rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
