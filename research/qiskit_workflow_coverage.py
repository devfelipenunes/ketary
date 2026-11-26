"""Paired workflow capability audit. Authored solutions, not human usability data.

Only trusted fixture strings are executed. Each native route must succeed and
match its stated oracle. Missing Ketary capability is explicit, never PASS.
"""
import argparse,json,ast,io,tokenize,time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit import Parameter,QuantumRegister,ClassicalRegister
from qiskit.circuit.library import QFTGate,StatePreparation,UnitaryGate,DiagonalGate,IGate,XXPlusYYGate
from qiskit.quantum_info import Operator,Statevector,SparsePauliOp,DensityMatrix
from qiskit.primitives import StatevectorEstimator

# id, objective, oracle, expected route, native source, Ketary source
CASES=[
("bell","Prepare and verify Bell correlations","numeric","direct",
"c=QuantumCircuit(2); c.h(0); c.cx(0,1); out=Statevector.from_instruction(c).expectation_value(SparsePauliOp('XX')).real",
"out=q.bell().run().math.expectation(q.X(0)@q.X(1))"),
("ghz","Construct four-qubit GHZ unitary","operator","direct",
"c=QuantumCircuit(4); c.h(0); c.cx([0,1,2],[1,2,3]); out=c",
"out=q.ghz(4)"),
("ordered_rotations","Apply aligned angles and overlapping ordered pairs","operator","direct",
"c=QuantumCircuit(4); c.ry(.3,2); c.ry(-.2,0); c.rzz(.4,2,1); c.rzz(-.5,1,0); out=c",
"out=q.Circuit(4).ry([.3,-.2],[2,0]).rzz([.4,-.5],pairs=[(2,1),(1,0)])"),
("remapped_blocks","Place two-wire block twice on nontrivial mappings","operator","direct",
"b=QuantumCircuit(2); b.h(0); b.cx(0,1); c=QuantumCircuit(4); c.compose(b,[3,1],inplace=True); c.compose(b,[0,2],inplace=True); out=c",
"out=q.Circuit(4).apply_each(q.bell(),placements=[(3,1),(0,2)])"),
("repeat","Repeat a nontrivial block five times","operator","direct",
"c=QuantumCircuit(2); c.ry(.3,0); c.cx(0,1); out=c.repeat(5)",
"out=q.Circuit(2).ry(.3,0).cx(0,1).repeat(5)"),
("inverse","Invert a nontrivial circuit","operator","direct",
"c=QuantumCircuit(2); c.ry(.3,0); c.cx(0,1); c.p(.2,1); out=c.inverse()",
"out=q.Circuit(2).ry(.3,0).cx(0,1).p(.2,1).inverse()"),
("basis","Prepare a bit label with reversible X gates","operator","direct",
"c=QuantumCircuit(4); c.x([0,2]); out=c",
"out=q.basis('0101')"),
("qft","Construct four-wire Fourier transform","operator","direct",
"c=QuantumCircuit(4); c.append(QFTGate(4),range(4)); out=c",
"out=q.qft(4)"),
("shared_binding","Bind one shared symbolic parameter","operator","direct",
"p=Parameter('t'); c=QuantumCircuit(2); c.ry(p,0); c.rzz(2*p,0,1); out=c.assign_parameters({p:.37})",
"p=q.Circuit.parameter('t'); out=q.Circuit.symbolic(2).ry(p,0).rzz(2*p,0,1).bind({p:.37})"),
("sweep","Evaluate a parameter grid with independent states","numeric","direct",
"p=Parameter('t'); c=QuantumCircuit(1); c.ry(p,0); out=[Statevector.from_instruction(c.assign_parameters({p:v})).probabilities()[1] for v in [.1,.4,.7]]",
"p=q.Circuit.parameter('t'); c=q.Circuit.symbolic(1).ry(p,0); out=[r.math.probability('1') for r in c.sweep(t=[.1,.4,.7]).run()]"),
("pauli_energy","Evaluate weighted Pauli energy","numeric","direct",
"c=QuantumCircuit(2); c.h(0); c.cx(0,1); H=SparsePauliOp.from_list([('XX',.8),('IZ',.5)]); out=Statevector.from_instruction(c).expectation_value(H).real",
"out=q.bell().run().math.expectation(.8*(q.X(0)@q.X(1))+.5*q.Z(0))"),
("reduced_state","Compute a one-wire reduced density matrix","numeric","direct",
"from qiskit.quantum_info import partial_trace\nc=QuantumCircuit(2); c.h(0); c.cx(0,1); out=partial_trace(Statevector.from_instruction(c),[1]).data",
"out=q.bell().run().math.density_matrix([0])"),
("variance","Evaluate variance of a real Pauli sum","numeric","direct",
"c=QuantumCircuit(2); c.ry(.3,0); c.cx(0,1); v=Statevector.from_instruction(c).data; H=SparsePauliOp.from_list([('XX',.8),('IZ',.5)]).to_matrix(); out=np.linalg.norm(H@v-np.vdot(v,H@v)*v)**2",
"out=q.Circuit(2).ry(.3,0).cx(0,1).run().math.variance(.8*(q.X(0)@q.X(1))+.5*q.Z(0))"),
("commuting_evolution","Exact commuting evolution including identity phase","operator","direct",
"c=QuantumCircuit(2); c.rzz(.6,0,1); c.global_phase=-.2; out=c",
"out=q.Circuit(2).evolve(.75*(q.Z(0)@q.Z(1))+.5,time=.4)"),
("phase_defect","Distinguish phase-error Bell state despite identical probabilities","numeric","direct",
"c=QuantumCircuit(2); c.h(0); c.cx(0,1); s=Statevector.from_instruction(c); c.z(0); t=Statevector.from_instruction(c); out=[np.allclose(s.probabilities(),t.probabilities()),np.isclose(t.expectation_value(SparsePauliOp('XX')),1)]",
"c=q.bell(); s=c.run(); t=c.z(0).run(); out=[s.math.probabilities()==t.math.probabilities(),t.test.expectation('XX',1).status=='PASS']"),
("qaoa","Two-layer weighted QAOA objective","numeric","direct",
"c=QuantumCircuit(4); c.h(range(4))\nfor g,b in [(.2,.3),(.4,.1)]:\n    for i,j,w in [(0,1,1.),(1,2,2.),(2,3,.5)]: c.rzz(-g*w,i,j)\n    c.rx(2*b,range(4))\nH=SparsePauliOp.from_list([('IIII',1.75),('IIZZ',-.5),('IZZI',-1.),('ZZII',-.25)]); out=Statevector.from_instruction(c).expectation_value(H).real",
"H=q.maxcut_hamiltonian(4,[(0,1),(1,2),(2,3)],weights=[1.,2.,.5]); c=q.Circuit(4).h(range(4))\nfor g,b in [(.2,.3),(.4,.1)]: c.evolve(H,time=g).rx(2*b,range(4))\nout=c.run().math.expectation(H)"),
("jacobian","Shared parameter derivative with chain rule","numeric","direct",
"def f(a,b):\n    c=QuantumCircuit(1); c.ry(a,0); c.ry(b,0); return Statevector.from_instruction(c).expectation_value(SparsePauliOp('Z')).real\nt=.37; out=(f(t+np.pi/2,2*t)-f(t-np.pi/2,2*t))/2+f(t,2*t+np.pi/2)-f(t,2*t-np.pi/2)",
"t=q.Circuit.parameter('t'); c=q.Circuit.symbolic(1).ry(t,0).ry(2*t,0); out=c.expectation_jacobian({t:.37},[q.Z(0)])[0][0]"),
("native_import","Import a supported native block","operator","interop",
"c=QuantumCircuit(2); c.h(0); c.cx(0,1); out=c",
"c=QuantumCircuit(2); c.h(0); c.cx(0,1); out=q.from_qiskit(c)"),
("native_lower_qft","Explicitly lower a QFTGate before import","operator","interop",
"c=QuantumCircuit(3); c.append(QFTGate(3),range(3)); out=c",
"c=QuantumCircuit(3); c.append(QFTGate(3),range(3)); out=q.from_qiskit(transpile(c,basis_gates=['u','cx'],optimization_level=0,qubits_initially_zero=False))"),
("native_lower_unitary","Explicitly synthesize a one-qubit unitary before import","operator","interop",
"c=QuantumCircuit(1); c.unitary(np.array([[0,1j],[1j,0]]),[0]); out=c",
"c=QuantumCircuit(1); c.unitary(np.array([[0,1j],[1j,0]]),[0]); out=q.from_qiskit(transpile(c,basis_gates=['u','cx'],optimization_level=0,qubits_initially_zero=False))"),
("bound_native_template","Bind a foreign native template on import","operator","interop",
"p=Parameter('t'); c=QuantumCircuit(1); c.ry(p,0); out=c.assign_parameters({p:.3})",
"p=Parameter('t'); c=QuantumCircuit(1); c.ry(p,0); out=q.Circuit.from_parameterized(c,{p:.3})"),
("arbitrary_unitary","Directly import a unitary matrix as a gate","operator","gap",
"c=QuantumCircuit(1); c.unitary(np.array([[0,1j],[1j,0]]),[0]); out=c",
"out=q.Circuit(1).append(UnitaryGate(np.array([[0,1j],[1j,0]])),[0])"),
("state_preparation","Direct arbitrary amplitude preparation block","state","gap",
"c=QuantumCircuit(2); c.append(StatePreparation([.5,.5j,.5,-.5j]),[0,1]); out=c",
"out=q.Circuit(2).append(StatePreparation([.5,.5j,.5,-.5j]),[0,1])"),
("partial_binding","Bind only one parameter while retaining another","parameters","gap",
"a,b=Parameter('a'),Parameter('b'); c=QuantumCircuit(1); c.ry(a,0); c.rz(b,0); out=c.assign_parameters({a:.3})",
"a,b=q.Circuit.parameter_vector('p',2); out=q.Circuit.symbolic(1).ry(a,0).rz(b,0).bind({a:.3})"),
("symbolic_import","Import native unbound symbolic circuit","parameters","gap",
"p=Parameter('t'); c=QuantumCircuit(1); c.ry(p,0); out=c",
"p=Parameter('t'); c=QuantumCircuit(1); c.ry(p,0); out=q.from_qiskit(c)"),
("open_control","Direct open-control native import","operator","gap",
"from qiskit.circuit.library import CXGate\nc=QuantumCircuit(2); c.append(CXGate(ctrl_state=0),[0,1]); out=c",
"from qiskit.circuit.library import CXGate\nout=q.Circuit(2).append(CXGate(ctrl_state=0),[0,1])"),
("composite_control","Direct controlled composite import including phase","operator","gap",
"b=QuantumCircuit(1); b.ry(.4,0); b.global_phase=.3; c=QuantumCircuit(2); c.append(b.to_gate().control(1),[0,1]); out=c",
"b=QuantumCircuit(1); b.ry(.4,0); b.global_phase=.3; out=q.Circuit(2).append(b.to_gate().control(1),[0,1])"),
("noncommuting_evolution","Explicit exact noncommuting evolution","operator","gap",
"from scipy.linalg import expm\nH=SparsePauliOp.from_list([('X',1.),('Z',1.)]); c=QuantumCircuit(1); c.unitary(expm(-.2j*H.to_matrix()),[0]); out=c",
"out=q.Circuit(1).evolve(q.X(0)+q.Z(0),time=.2)"),
("complex_operator","Import complex non-Hermitian Pauli operator","numeric","gap",
"out=SparsePauliOp.from_list([('X',1j),('Z',.3)]).to_matrix()",
"out=q.Observable.from_qiskit(SparsePauliOp.from_list([('X',1j),('Z',.3)])).to_qiskit().to_matrix()"),
("metadata","Preserve native circuit metadata on import","operator","gap",
"c=QuantumCircuit(1); c.h(0); c.metadata={'experiment':'a'}; out=c",
"c=QuantumCircuit(1); c.h(0); c.metadata={'experiment':'a'}; out=q.from_qiskit(c)"),
("barrier","Import a circuit with a barrier","state","gap",
"c=QuantumCircuit(1); c.h(0); c.barrier(); c.h(0); out=c",
"c=QuantumCircuit(1); c.h(0); c.barrier(); c.h(0); out=q.from_qiskit(c)"),
("mixed_state","Represent mixed-state density matrix","numeric","gap",
"out=DensityMatrix(np.eye(2)/2).data",
"out=q.Result(np.eye(2)/2).math.density_matrix()"),
("dynamic_import","Import a native measured circuit with feedforward","sequence","gap",
"c=QuantumCircuit(2,1); c.h(0); c.measure(0,0)\nwith c.if_test((c.clbits[0],1)): c.x(1)\nout=c",
"c=QuantumCircuit(2,1); c.h(0); c.measure(0,0)\nwith c.if_test((c.clbits[0],1)): c.x(1)\nout=q.from_qiskit(c)"),
("multiple_classical_registers","Native import with two classical registers","sequence","gap",
"c=QuantumCircuit(QuantumRegister(2),ClassicalRegister(1,'a'),ClassicalRegister(1,'b')); c.measure([0,1],[0,1]); out=c",
"c=QuantumCircuit(QuantumRegister(2),ClassicalRegister(1,'a'),ClassicalRegister(1,'b')); c.measure([0,1],[0,1]); out=q.from_qiskit(c)"),
("identity_gate","Import native identity instruction","operator","gap",
"c=QuantumCircuit(1); c.id(0); out=c",
"out=q.Circuit(1).append(IGate(),[0])"),
("xx_plus_yy","Import XX+YY entangling gate","operator","gap",
"c=QuantumCircuit(2); c.append(XXPlusYYGate(.4,.2),[0,1]); out=c",
"out=q.Circuit(2).append(XXPlusYYGate(.4,.2),[0,1])"),
("estimator","Use Qiskit primitive to evaluate a Ketary-authored circuit","numeric","interop",
"c=QuantumCircuit(1); c.ry(.3,0); out=float(StatevectorEstimator().run([(c,SparsePauliOp('Z'))]).result()[0].data.evs)",
"c=q.Circuit(1).ry(.3,0); out=float(StatevectorEstimator().run([(c.to_qiskit(),q.Z(0).to_qiskit())]).result()[0].data.evs)"),
]

# Recovery routes for six rejected direct operations. These are the same
# mathematical tasks, not six additional independent capabilities.
CASES.extend([
("recovery_open_control","Implement open control by explicit conjugation","operator","direct",
"from qiskit.circuit.library import CXGate\nc=QuantumCircuit(2); c.append(CXGate(ctrl_state=0),[0,1]); out=c",
"out=q.Circuit(2).x(0).cx(0,1).x(0)"),
("recovery_composite_control","Controlled rotation with strict relative phase","operator","direct",
"b=QuantumCircuit(1); b.ry(.4,0); b.global_phase=.3; c=QuantumCircuit(2); c.append(b.to_gate().control(1),[0,1]); out=c",
"out=q.Circuit(2).cry(.4,0,1).p(.3,0)"),
("recovery_noncommuting_evolution","Exact one-qubit noncommuting Hamiltonian by analytic basis change","operator","direct",
"from scipy.linalg import expm\nH=SparsePauliOp.from_list([('X',1.),('Z',1.)]); c=QuantumCircuit(1); c.unitary(expm(-.2j*H.to_matrix()),[0]); out=c",
"out=q.Circuit(1).ry(-np.pi/4,0).rz(.4*np.sqrt(2),0).ry(np.pi/4,0)"),
("recovery_identity_gate","Logical operator identity without preserving instruction count","operator","direct",
"c=QuantumCircuit(1); c.id(0); out=c",
"out=q.Circuit(1)"),
("recovery_state_preparation","Explicit unitary lowering of StatePreparation, not reset","operator","interop",
"c=QuantumCircuit(2); c.append(StatePreparation([.5,.5j,.5,-.5j]),[0,1]); out=c",
"c=QuantumCircuit(2); c.append(StatePreparation([.5,.5j,.5,-.5j]),[0,1]); out=q.from_qiskit(transpile(c,basis_gates=['u','cx'],optimization_level=0,qubits_initially_zero=False))"),
("recovery_xx_plus_yy","Explicit native lowering of XX+YY entangler","operator","interop",
"c=QuantumCircuit(2); c.append(XXPlusYYGate(.4,.2),[0,1]); out=c",
"c=QuantumCircuit(2); c.append(XXPlusYYGate(.4,.2),[0,1]); out=q.from_qiskit(transpile(c,basis_gates=['u','cx'],optimization_level=0,qubits_initially_zero=False))"),
])

def shape(s):
    tree=ast.parse(s)
    return dict(tokens=sum(t.type not in (tokenize.ENDMARKER,tokenize.NEWLINE,tokenize.NL,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT) for t in tokenize.generate_tokens(io.StringIO(s).readline)),calls=sum(isinstance(n,ast.Call) for n in ast.walk(tree)),statements=sum(isinstance(n,ast.stmt) for n in ast.walk(tree)))
def execute(s):
    env=globals().copy();start=time.perf_counter_ns();exec(compile(s,"<authored-workflow>","exec"),env);return env["out"],(time.perf_counter_ns()-start)/1e6
def convert(out,kind):
    if isinstance(out,q.Circuit):out=out.to_qiskit()
    if kind=="operator":return Operator(out).data
    if kind=="state":return Statevector.from_instruction(out).data
    if kind=="parameters":return len(out.parameters)
    if kind=="sequence":return (out.num_qubits,out.num_clbits,len(out.data))
    return np.asarray(out)
def evaluate(case):
    key,objective,kind,route,native,sdk=case
    a,t=execute(native);want=convert(a,kind)
    row=dict(id=key,objective=objective,oracle=kind,expected_route=route,native=dict(source=native,**shape(native),ms=t))
    try:
        b,u=execute(sdk)
    except (q.UnsupportedOperation,q.ResourceLimit,ValueError,TypeError) as exc:
        if route!="gap":raise
        row.update(status="rejected",exception=type(exc).__name__,reason=str(exc),ketary=dict(source=sdk,**shape(sdk)))
        return row
    got=convert(b,kind)
    np.testing.assert_allclose(got,want,atol=1e-9,rtol=0)
    row.update(status="matched",max_error=float(np.max(np.abs(np.asarray(got,dtype=complex)-np.asarray(want,dtype=complex)))),ketary=dict(source=sdk,**shape(sdk),ms=u))
    return row
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path);p.add_argument("--prompts",action="store_true");a=p.parse_args()
    if a.prompts:
        print(json.dumps([dict(id=c[0],task=c[1],oracle=c[2]) for c in CASES],indent=2));return
    rows=[evaluate(c) for c in CASES]
    for row in rows:print(json.dumps(row,allow_nan=False))
    if a.output:a.output.write_text(json.dumps(dict(scope="authored task routes; gaps mean tested direct route rejected, not impossibility; no human or LLM participants",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
