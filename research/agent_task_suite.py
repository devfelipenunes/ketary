"""Held-out authored task fixtures; not a human/LLM experiment.

--prompts emits only task descriptions. Default executes the two trusted
reference implementations and compares exact semantics and lexical metrics.
Never executes externally supplied model responses.
"""
import argparse
import json
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Operator, Statevector, Pauli
from circuit_writing_study import metrics

TASKS=[
("overlap_direction","On five wires, apply H to wire 4; then CX to ordered pairs (4,1), (1,0), (0,4), (4,1). Preserve order and repeated pair.", "operator",
"""c=QuantumCircuit(5)
c.h(4)
c.cx([4,1,0,4],[1,0,4,1])
out=c""",
"""out=q.Circuit(5).h(4).cx(pairs=[(4,1),(1,0),(0,4),(4,1)])"""),
("shared_layer","Build a reusable three-wire layer with RY(.2) on local 0 and CX chain; apply twice on (5,2,0), then once on (1,3,4).", "operator",
"""layer=QuantumCircuit(3)
layer.ry(.2,0)
layer.cx([0,1],[1,2])
c=QuantumCircuit(6)
for wires in [(5,2,0),(5,2,0),(1,3,4)]:
    c.compose(layer,qubits=wires,inplace=True)
out=c""",
"""layer=q.Circuit(3).ry(.2,0).cx(pairs=q.chain(range(3)))
out=q.Circuit(6).apply_each(layer,placements=[(5,2,0),(5,2,0),(1,3,4)])"""),
("ordered_angles","Apply RZ angles .1,-.2,.7 to wires 3,0,2 in that order; then a star CZ centered at wire 3 with targets 0,1,2.", "operator",
"""c=QuantumCircuit(4)
for angle,wire in zip([.1,-.2,.7],[3,0,2]):
    c.rz(angle,wire)
c.cz(3,[0,1,2])
out=c""",
"""out=q.Circuit(4).rz([.1,-.2,.7],[3,0,2]).cz(pairs=q.star([3,0,1,2]))"""),
("symbolic_shared","Create one parameter theta; a two-wire RY(theta), CX layer is applied to (2,0) and (1,2) with the SAME parameter; then bind .43.", "operator",
"""theta=Parameter("theta")
layer=QuantumCircuit(2)
layer.ry(theta,0)
layer.cx(0,1)
c=QuantumCircuit(3)
for wires in [(2,0),(1,2)]:
    c.compose(layer,qubits=wires,inplace=True)
out=c.assign_parameters({theta:.43})""",
"""theta=q.Circuit.parameter("theta")
layer=q.Circuit.symbolic(2).ry(theta,0).cx(0,1)
out=q.Circuit.symbolic(3).apply_each(layer,placements=[(2,0),(1,2)]).bind(theta=.43)"""),
("reversible_prefix","On four wires, compute CX(3,0), apply RZ(.6) to wire 0, uncompute CX(3,0). Preserve strict phase.", "operator",
"""c=QuantumCircuit(4)
c.cx(3,0)
c.rz(.6,0)
c.cx(3,0)
out=c""",
"""out=q.Circuit(4).compute_action_uncompute(q.Circuit(2).cx(0,1),q.Circuit(1).rz(.6,0),compute_wires=[3,0],action_wires=[0])"""),
("dynamic_readout","On four qubits and four classical bits, H on 3 and 0, measure (3,0) into bits (1,2), reset (3,0), then measure wire 3 into bit 0.", "sequence",
"""c=QuantumCircuit(4,4)
c.h([3,0])
c.measure([3,0],[1,2])
c.reset([3,0])
c.measure(3,0)
out=c""",
"""out=q.Circuit.classical(4,4).h([3,0]).measure([3,0],[1,2]).reset([3,0]).measure(3,0)"""),
("pauli_queries","Prepare three-wire GHZ and return ordered expectations XXX, ZZI, IZZ, XXX (including the repeated term).", "numeric",
"""c=QuantumCircuit(3)
c.h(0)
c.cx([0,1],[1,2])
r=Statevector.from_instruction(c)
out=tuple(float(r.expectation_value(Pauli(label)).real) for label in ["XXX","ZZI","IZZ","XXX"])""",
"""out=q.ghz(3).run().math.expectations(["XXX","ZZI","IZZ","XXX"])"""),
("complex_input","Evolve normalized state (|00> + i|11>)/sqrt(2) by H(1), CX(1,0), and RZ(.2,0). Return the full complex vector.", "numeric",
"""c=QuantumCircuit(2)
c.h(1)
c.cx(1,0)
c.rz(.2,0)
out=Statevector(np.array([1,0,0,1j])/np.sqrt(2)).evolve(c).data""",
"""out=q.Circuit(2).h(1).cx(1,0).rz(.2,0).run(initial_state=np.array([1,0,0,1j])/np.sqrt(2)).math.statevector()"""),
]


def validate(expected,observed,oracle):
    if isinstance(observed,q.Circuit):
        observed=observed.to_qiskit()
    if oracle=="sequence":
        if expected!=observed:
            raise AssertionError("native sequence mismatch")
        return 0.0
    if oracle=="operator":
        expected,observed=Operator(expected).data,Operator(observed).data
    left,right=np.asarray(expected),np.asarray(observed)
    if left.shape!=right.shape:
        raise AssertionError("output shape mismatch")
    np.testing.assert_allclose(left,right,atol=1e-10,rtol=0)
    return float(np.max(np.abs(left-right)))


def run():
    result=[]
    for key,prompt,oracle,native,sdk in TASKS:
        env={"q":q,"np":np,"QuantumCircuit":QuantumCircuit,"Parameter":Parameter,
             "Statevector":Statevector,"Pauli":Pauli}
        a,b=env.copy(),env.copy()
        exec(compile(native,key+":native","exec"),a)
        exec(compile(sdk,key+":ketary","exec"),b)
        error=validate(a["out"],b["out"],oracle)
        result.append({"id":key,"oracle":oracle,"native":metrics(native),"ketary":metrics(sdk),
                       "max_error":error,"matched":True})
    return {"scope":"authored reference solutions only; no model or human participants",
            "tasks":result,"native_tokens":sum(x["native"]["tokens"] for x in result),
            "ketary_tokens":sum(x["ketary"]["tokens"] for x in result)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prompts",action="store_true")
    args=p.parse_args()
    print(json.dumps([{"id":t[0],"prompt":t[1],"oracle":t[2]} for t in TASKS]
                     if args.prompts else run(),indent=2,allow_nan=False))
