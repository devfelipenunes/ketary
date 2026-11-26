"""Authored matched workloads inspired by published benchmark families.

No upstream source is copied; native library factories are used when they
are a fair baseline. Token counts are source proxies, not human outcomes.
"""
import ast
import io
import json
import tokenize
import numpy as np
import ketary as q
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.library import real_amplitudes, efficient_su2
from qiskit.synthesis import synth_qft_full

CASES=[
("ghz_chain",
"""c=QuantumCircuit(4)
c.h(3)
c.cx([3,2,1],[2,1,0])""",
"""c=q.Circuit(4).h(3).cx(pairs=q.chain(reversed(range(4))))"""),
("graph_ring",
"""c=QuantumCircuit(4)
c.h(range(4))
c.cz([0,1,2,3],[1,2,3,0])""",
"""c=q.Circuit(4).h(range(4)).cz(pairs=q.ring(range(4)))"""),
("real_amplitudes",
     "c=real_amplitudes(4,entanglement='linear',reps=2).assign_parameters(angles)",
     "c=q.ansatz(4,reps=2).bind(angles)"),
    ("efficient_su2",
     "c=efficient_su2(4,entanglement='linear',reps=1).assign_parameters(su2_angles)",
     "c=q.ansatz(4,rotations=('ry','rz')).bind(su2_angles)"),
    ("qaoa_cost_mixer",
"""c=QuantumCircuit(4)
c.h(range(4))
for gamma,beta in [(0.2,0.3),(0.4,0.5)]:
    c.rzz(2*gamma,[0,1,2,3],[1,2,3,0])
    c.rx(2*beta,range(4))""",
"""c=q.Circuit(4).h(range(4))
for gamma,beta in [(0.2,0.3),(0.4,0.5)]:
    c.rzz(2*gamma,pairs=q.ring(c.wires)).rx(2*beta,c.wires)"""),
("qft",
"""c=synth_qft_full(4)""",
"""c=q.qft(4)"""),
("rotation_layer",
"""c=QuantumCircuit(4)
for w,a in zip(range(4),angles[:4]): c.ry(a,w)""",
"""c=q.Circuit(4)
c.ry(angles[:4],c.wires)"""),
("repeat_layer",
"""layer=QuantumCircuit(4)
layer.h(range(4))
layer.cx(0,1)
c=layer.repeat(4)""",
"""layer=q.Circuit(4).h(range(4)).cx(0,1)
c=layer.repeat(4)"""),
]

def metrics(source):
    excluded={tokenize.ENCODING,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,
              tokenize.DEDENT,tokenize.ENDMARKER,tokenize.COMMENT}
    tree=ast.parse(source)
    return {"tokens":sum(t.type not in excluded for t in tokenize.generate_tokens(io.StringIO(source).readline)),
            "calls":sum(isinstance(x,ast.Call) for x in ast.walk(tree)),
            "loops":sum(isinstance(x,(ast.For,ast.While,ast.comprehension)) for x in ast.walk(tree))}

def run():
    results=[]
    for name,native,ketary in CASES:
        env={"QuantumCircuit":QuantumCircuit,"real_amplitudes":real_amplitudes,
             "efficient_su2":efficient_su2,"synth_qft_full":synth_qft_full,"q":q,
             "angles":np.linspace(.1,1.2,12).tolist(),
             "su2_angles":np.linspace(.1,1.6,16).tolist()}
        exec(compile(native,name+":native","exec"),env)
        expected=env.pop("c")
        exec(compile(ketary,name+":ketary","exec"),env)
        observed=env["c"].to_qiskit()
        error=float(np.max(np.abs(Operator(expected).data-Operator(observed).data)))
        results.append({"case":name,"native":metrics(native),"ketary":metrics(ketary),
                        "native_gates":len(expected.data),"ketary_gates":len(observed.data),
                        "max_operator_element_error":error,"matched":error<=1e-10})
    return {"qiskit":qiskit.__version__,"cases":results,
            "matched":sum(row["matched"] for row in results),
            "total":len(results),"native_tokens":sum(row["native"]["tokens"] for row in results),
            "ketary_tokens":sum(row["ketary"]["tokens"] for row in results)}
if __name__=="__main__":
    print(json.dumps(run(),indent=2,allow_nan=False))
