"""Paired authored source snippets; semantic oracles, not human productivity.

All snippets run as Python. The baseline uses APIs available before DX.
Counts describe these snippets only. Native comparison uses the full operator
or native state/expected mathematical oracle where applicable.
"""
import ast
import io
import json
import tokenize
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Operator, Statevector, Pauli

CASES=[
("batch",
"""c=q.Circuit(4)
for w in [0,2,3]: c.h(w)
result=c""",
"""c=q.Circuit(4).h([0,2,3])
result=c"""),
("block",
"""c=q.Circuit(4)
c=c.compose(q.bell(),wires=[0,2])
result=c""",
"""c=q.Circuit(4).apply(q.bell(),wires=[0,2])
result=c"""),
("named_wires",
"""c=q.Circuit(4)
c.h_many([0,2]).cx(0,2)
result=c""",
"""c=q.Circuit(4)
pair=c.register('pair',[0,2])
c.h(pair).cx(*pair)
result=c"""),
("local_pauli",
"""r=q.ghz(4).run()
result=r.math.expectation('ZIZI')""",
"""r=q.ghz(4).run()
result=r.math.expectation({3:'Z',1:'Z'})"""),
("contract",
"""c=q.bell()
result=q.Contract(2,expectations={'XX':1}).verify(c.run()).status""",
"""c=q.bell()
result=c.contract(expectations={'XX':1}).verify(c.run()).status"""),
("evidence",
"""a=q.bell(); b=a.copy().z(0)
report=b.test.compare(a)
e=q.Evidence.from_json(json.dumps(report['evidence']))
result=e.reproduce()['reproduced']""",
"""a=q.bell(); b=a.copy().z(0)
report=b.test.compare(a)
e=report.evidence
result=e.reproduce()['reproduced']"""),
("checkpoint",
"""c=q.bell()
c.z(0)
result=c.debug.verify_checkpoints({2:q.Contract(2,expectations={'XX':1}),3:q.Contract(2,expectations={'XX':1})})['status']""",
"""c=q.bell().checkpoint('before').z(0).checkpoint('after')
check=c.contract(expectations={'XX':1})
result=c.debug.verify_checkpoints({'before':check,'after':check}).status"""),
("binding",
"""theta=q.Circuit.parameter('theta')
c=q.Circuit.symbolic(1).ry(theta,0)
result=c.bind({theta:.4})""",
"""theta=q.Circuit.parameter('theta')
c=q.Circuit.symbolic(1).ry(theta,0)
result=c.bind(theta=.4)"""),
("sweep",
"""theta=q.Circuit.parameter('theta')
c=q.Circuit.symbolic(1).ry(theta,0)
result=tuple(c.bind({theta:v}).run().math.probability('0') for v in [0,.4,.8])""",
"""theta=q.Circuit.parameter('theta')
c=q.Circuit.symbolic(1).ry(theta,0)
result=tuple(r.math.probability('0') for r in c.sweep(theta=[0,.4,.8]).run())"""),
("qpe_decode",
"""r=q.phase_estimation(.375,precision=3).run()
p=r.math.marginal_probabilities([2,1,0])
result=int(max(p,key=p.get),2)/8""",
"""r=q.phase_estimation(.375,precision=3).run()
result=q.decode_phase_estimation(r,precision=3)['phase']"""),
("reversible",
"""c=q.Circuit(2); u=q.Circuit(2).cx(0,1); v=q.Circuit(1).z(0)
result=c.compose(u,wires=[0,1]).compose(v,wires=[1]).compose(u.inverse(),wires=[0,1])""",
"""c=q.Circuit(2); u=q.Circuit(2).cx(0,1); v=q.Circuit(1).z(0)
result=c.compute_action_uncompute(u,v,compute_wires=[0,1],action_wires=[1])""")
]


def execute(source):
    ns={"q":q,"json":json,"QuantumCircuit":QuantumCircuit,"Parameter":Parameter,"Statevector":Statevector,"Pauli":Pauli}
    exec(compile(source,"<authored-example>","exec"),ns)
    return ns["result"]

def count(source):
    tree=ast.parse(source)
    ignored={tokenize.ENCODING,tokenize.ENDMARKER,tokenize.INDENT,tokenize.DEDENT,tokenize.NEWLINE,tokenize.NL,tokenize.COMMENT}
    return {"tokens":sum(t.type not in ignored for t in tokenize.generate_tokens(io.StringIO(source).readline)),
            "calls":sum(isinstance(n,ast.Call) for n in ast.walk(tree)),
            "numeric_literals":sum(isinstance(n,ast.Constant) and type(n.value) in (int,float) for n in ast.walk(tree))}

NATIVE={
"batch": """c=QuantumCircuit(4)
c.h([0,2,3])
result=c""",
"block": """bell=QuantumCircuit(2)
bell.h(0); bell.cx(0,1)
c=QuantumCircuit(4)
c.compose(bell,qubits=[0,2],inplace=True)
result=c""",
"local_pauli": """c=QuantumCircuit(4)
c.h(0)
for w in range(1,4): c.cx(w-1,w)
result=float(Statevector.from_instruction(c).expectation_value(Pauli('ZIZI')).real)""",
"binding": """theta=Parameter('theta')
c=QuantumCircuit(1)
c.ry(theta,0)
result=c.assign_parameters({theta:.4})""",
"reversible": """c=QuantumCircuit(2); u=QuantumCircuit(2); v=QuantumCircuit(1)
u.cx(0,1); v.z(0)
c.compose(u,qubits=[0,1],inplace=True)
c.compose(v,qubits=[1],inplace=True)
c.compose(u.inverse(),qubits=[0,1],inplace=True)
result=c"""
}

def run():
    rows=[]
    for name,old,new in CASES:
        left,right=execute(old),execute(new)
        if isinstance(left,q.Circuit):
            np.testing.assert_allclose(Operator(left.to_qiskit()).data,Operator(right.to_qiskit()).data,atol=1e-12,rtol=0)
        elif isinstance(left,(float,tuple)):
            np.testing.assert_allclose(left,right,atol=1e-12,rtol=0)
        else:
            assert left==right,name
        row={"case":name,"baseline":count(old),"candidate":count(new),"equivalent":True}
        if name in NATIVE:
            native=execute(NATIVE[name])
            if isinstance(left,q.Circuit):
                np.testing.assert_allclose(Operator(left.to_qiskit()).data,Operator(native).data,atol=1e-12,rtol=0)
            else:
                np.testing.assert_allclose(left,native,atol=1e-12,rtol=0)
            row["qiskit"]=count(NATIVE[name])
        rows.append(row)
    return {"scope":"11 authored matched snippets, source counts not productivity; no independent human evaluation",
            "rows":rows,"equivalent":len(rows),"native_matched":sum("qiskit" in r for r in rows),"baseline_tokens":sum(r["baseline"]["tokens"] for r in rows),
            "candidate_tokens":sum(r["candidate"]["tokens"] for r in rows)}

if __name__=="__main__":
    print(json.dumps(run(),indent=2))
