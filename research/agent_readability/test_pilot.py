"""Paired reference snippets authored with both APIs visible.

Counts are lexical Python tokens, not LLM tokens. These are correctness and
ergonomics fixtures, not independent model trials. Only checked-in snippets
are executed; do not execute untrusted generated Python in this process.
"""
import io
import json
import tokenize
from pathlib import Path
import numpy as np
import pytest
import ketary as q
from agent_prototype import inspect_circuit, evidence, checks, read_literal_source

CASES={
"bell_probabilities":{
"native":"""from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
c=QuantumCircuit(2)
c.h(0)
c.cx(0,1)
p=Statevector.from_instruction(c).probabilities_dict()
answer=[float(p.get('00',0)),float(p.get('11',0))]""",
"ketary":"""import ketary as q
r=q.bell().run()
answer=[r.math.probability('00'),r.math.probability('11')]""",
"candidate":"""import ketary as q
from agent_prototype import evidence
report=evidence(q.bell().run(),bits=['00','11'])
answer=list(report['probabilities'].values())""",
"expected":[.5,.5]},
"relative_phase":{
"native":"""import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
c=QuantumCircuit(2)
c.h(0)
c.cx(0,1)
a=Statevector.from_instruction(c)
c.z(0)
b=Statevector.from_instruction(c)
answer=[bool(np.allclose(a.probabilities(),b.probabilities())),float(abs(np.vdot(a.data,b.data))**2)]""",
"ketary":"""import ketary as q
c=q.bell()
a=c.run()
c.gates.z(0)
b=c.run()
answer=[a.test.distribution(b).status=='PASS',a.math.fidelity(b)]""",
"candidate":"""import ketary as q
from agent_prototype import checks
c=q.bell()
a=c.run()
c.gates.z(0)
b=c.run()
report=checks(distribution=a.test.distribution(b),state=a.test.state(b))
answer=[report['checks']['distribution']['status']=='PASS',a.math.fidelity(b)]""",
"expected":[True,0]},
"read_operation_order":{
"native":"""from qiskit import QuantumCircuit
c=QuantumCircuit(3)
c.h(2)
c.cx(2,0)
c.ry(.4,1)
answer=[(i.operation.name,[c.find_bit(w).index for w in i.qubits],[float(p) for p in i.operation.params]) for i in c.data]""",
"ketary":"""import json
import ketary as q
c=q.Circuit(3).gates.h(2).gates.cx(2,0).gates.ry(.4,1)
answer=[(i['gate'],i['wires'],i['params']) for i in json.loads(c.to_json())['operations']]""",
"candidate":"""import ketary as q
from agent_prototype import inspect_circuit
c=q.Circuit(3).gates.h(2).gates.cx(2,0).gates.ry(.4,1)
answer=[(i['gate'],i['wires'],i['params']) for i in inspect_circuit(c)['operations']]""",
"expected":[["h",[2],[]],["cx",[2,0],[]],["ry",[1],[.4]]]},
"state_not_operator":{
"native":"""import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator
a=QuantumCircuit(1)
b=QuantumCircuit(1)
b.z(0)
answer=[bool(np.allclose(Statevector.from_instruction(a).data,Statevector.from_instruction(b).data)),bool(np.allclose(Operator(a).data,Operator(b).data))]""",
"ketary":"""import ketary as q
a=q.Circuit(1)
b=q.Circuit(1).gates.z(0)
answer=[a.run().test.state(b.run()).status=='PASS',a.test.equivalent(b).status=='PASS']""",
"candidate":"""import ketary as q
from agent_prototype import checks
a=q.Circuit(1)
b=q.Circuit(1).gates.z(0)
report=checks(state=a.run().test.state(b.run()),operator=a.test.equivalent(b))
answer=[report['checks'][k]['status']=='PASS' for k in ('state','operator')]""",
"expected":[True,False]},
"diagnose_relative_phase":{
"native":"""import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
a=QuantumCircuit(2)
a.h(0)
a.cx(0,1)
b=a.copy()
a.x(0)
b.z(0)
x=Statevector.from_int(0,4)
y=Statevector.from_int(0,4)
answer=None
for i,(u,v) in enumerate(zip(a.data,b.data),1):
    x=x.evolve(u.operation,qargs=[a.find_bit(w).index for w in u.qubits])
    y=y.evolve(v.operation,qargs=[b.find_bit(w).index for w in v.qubits])
    if not x.equiv(y):
        answer=i
        break""",
"ketary":"""import ketary as q
a=q.bell().gates.x(0)
b=q.bell().gates.z(0)
answer=b.debug.compare(a).step_index""",
"candidate":"""import ketary as q
from dataclasses import asdict
a=q.bell().gates.x(0)
b=q.bell().gates.z(0)
report=asdict(b.debug.compare(a))
answer=report['step_index']""",
"expected":3},
}
def token_count(code):
    return sum(t.type not in (tokenize.ENCODING,tokenize.ENDMARKER,tokenize.NEWLINE,tokenize.NL,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT) for t in tokenize.generate_tokens(io.StringIO(code).readline))

def normalize(x):
    return json.loads(json.dumps(x))

@pytest.mark.parametrize("case",CASES)
@pytest.mark.parametrize("variant",["native","ketary","candidate"])
def test_reference_snippets(case,variant):
    data=CASES[case]
    scope={}
    exec(compile(data[variant],"<trusted research fixture>","exec"),scope)
    actual,expected=normalize(scope["answer"]),data["expected"]
    if case in ("bell_probabilities","relative_phase"):
        np.testing.assert_allclose(actual,expected,atol=1e-12)
    else:
        assert actual==expected

@pytest.mark.parametrize("source",[
"import ketary as q\nc=q.Circuit(3)\nc.gates.h(2)\nc.gates.cx(2,0)\nc.gates.ry(.4,1)",
"import ketary as q\nc=q.Circuit(3)\nc.gates.h(2).gates.cx(2,0).gates.ry(.4,1)",
])
def test_static_read_matches_runtime(source):
    report=read_literal_source(source)
    assert report["status"]=="PASS"
    # Execute ONLY the fixed checked-in fixture to validate extraction.
    scope={};exec(source,scope)
    actual=inspect_circuit(scope["c"])["operations"]
    assert [{k:v for k,v in row.items() if k not in ("line","column")} for row in report["operations"]]==actual
    assert all(row["line"]>=3 for row in report["operations"])

@pytest.mark.parametrize("source",[
"import ketary as q\nc=q.Circuit(3)\nfor i in range(3): c.gates.h(i)",
"import ketary as q\nc=q.Circuit(3)\nc.gates.rx(theta,0)",
"import ketary as q\nc=q.Circuit(3)\nc.gates.cx(1,1)",
"import ketary as q\nc=q.Circuit(3)\nc.run()",
"import os\nc=q.Circuit(3)",
"import ketary as q\nc=q.Circuit(3)\nc.gates.h(__import__('os').system('echo SHOULD_NOT_EXECUTE'))",
])
def test_static_reader_abstains(source):
    assert read_literal_source(source)["status"]=="UNSUPPORTED"

def test_inspection_and_evidence_bounds(monkeypatch):
    c=q.bell();r=c.run();before=c.to_qiskit()
    def fail(*a,**k): raise AssertionError("unexpected run")
    monkeypatch.setattr(q.Circuit,"run",fail)
    info=inspect_circuit(c,max_operations=1)
    assert info["omitted"]==1 and info["operations"][0]["gate"]=="h"
    assert c.to_qiskit()==before
    report=evidence(r,bits=["00"],paulis=["ZZ"])
    assert report["expectations"]["ZZ"]==pytest.approx(1)
    assert json.loads(json.dumps(report))==report
    with pytest.raises(ValueError): evidence(r,bits=["00"]*33)
    assert checks(operator=q.Circuit(9).test.equivalent(q.Circuit(9)))["status"]=="UNSUPPORTED"

if __name__=="__main__":
    report={name:{k:{"tokens":token_count(v),"lines":len(v.splitlines())} for k,v in values.items() if k!="expected"} for name,values in CASES.items()}
    print(json.dumps(report,indent=2))
