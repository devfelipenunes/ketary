"""Run from isolated installed local wheels with python -I; no source imports."""
import importlib.metadata as md
import json,sys,time
from dataclasses import replace
from fractions import Fraction
from qiskit import QuantumCircuit
from qcontract import Pauli,Contract,StateEigen,CleanInput,Separable,ZBranch,SumTransition,NoiseAfter,Correctable,prepare

def main():
    checks=0
    def check(ok):
        nonlocal checks
        assert ok;checks+=1
    def reject(f):
        nonlocal checks
        try:f()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError("unsupported input accepted")
    try:md.version("ketary")
    except md.PackageNotFoundError:checks+=1
    else:raise AssertionError("legacy distribution installed")
    c=QuantumCircuit(2);c.h(0);c.cx(0,1)
    p=prepare(c,prepare_state=True);x=Pauli("XX");z=Pauli("IZ")
    good=Contract(requires=z,ensures=x);bad=Contract(requires=z,ensures=Pauli("-XX"))
    r=p.verify(good,bad,StateEigen(x),Separable(1),CleanInput((1,)))
    check([v.status for v in r]==["PASS","FAIL","PASS","FAIL","FAIL"])
    check(r[1].witness is not None)
    check(p.replay(good,r[0]) is True)
    check(p.replay(bad,r[1]) is True)
    check(p.replay(good,r[0],max_work=1) is None)
    check(p.replay(bad,replace(r[1],witness=None)) is False)
    check(p.replay(good,r[1]) is False)
    check(r[0].domain!=r[2].domain and r[0].snapshots==(p.snapshot_id,))
    check(p.replay(StateEigen(x),r[2]) is True)
    check(p.replay(StateEigen(x),replace(r[2],expectation=((0,0),0))) is False)
    check(p.replay(StateEigen(x),replace(r[2],status="FAIL")) is False)
    check(sum(v.reserved for v in r)<=2_000_000)
    check(p.verify(good,bad,max_work=1)[0].status=="INCONCLUSIVE")
    original=p.snapshot_id;c.x(0)
    check(p.check(good).status=="PASS" and prepare(c).snapshot_id!=original)
    same=QuantumCircuit(2);same.h(0);same.cx(0,1)
    ref=prepare(same)
    check(p.check(p.equivalent_to(ref)).status=="PASS")
    check(p.check(p.equivalent_to(ref,strict=True)).status=="PASS")
    check(p.check(p.action_matches(ref,ancillas=(1,))).status=="PASS")
    # Bell measurement branch probability and unnormalized Z expectation.
    half=((1,0),1)
    branch=p.check(ZBranch(0,0,z,half,half))
    check(branch.status=="PASS")
    check(dict(branch.diagnostics)=={"probability":half,"unnormalized_expectation":half})
    one=QuantumCircuit(3);one.h(0);q=prepare(one);a=Pauli("IIX");b=Pauli("IIZ");i=Pauli("III")
    s=SumTransition(((b,Fraction(1,3)),),((a,Fraction(1,3)),))
    check(q.check(s).status=="PASS")
    n=NoiseAfter(b,a,((i,3),(b,1)),4,Fraction(1,2))
    noise=q.check(n)
    check(noise.status=="PASS")
    check(dict(noise.diagnostics)["coefficient"]==(1,2))
    st=(Pauli("IZZ"),Pauli("ZZI"));es=(i,Pauli("IIX"),Pauli("IXI"),Pauli("XII"))
    code=q.check(Correctable(st,es))
    check(code.status=="PASS" and code.snapshots==())
    check(len(dict(code.diagnostics)["table"])==4)
    check(q.check(Correctable(st,es+(Pauli("XXX"),))).status=="FAIL")
    # Real algorithm-shaped circuits in the admitted alphabet: GHZ and
    # Bernstein-Vazirani phase oracle. Independent expected outputs.
    for width in (4,8,16,32,64):
        g=QuantumCircuit(width);g.h(0)
        for j in range(1,width):g.cx(0,j)
        ghz=prepare(g)
        check(ghz.check(StateEigen(Pauli("X"*width))).status=="PASS")
        check(ghz.check(StateEigen(Pauli("-"+"X"*width))).status=="FAIL")
    for bits in ("101","1001","111001"):
        width=len(bits);v=QuantumCircuit(width)
        for j in range(width):v.h(j)
        for j,bit in enumerate(reversed(bits)):
            if bit=="1":v.z(j)
        for j in range(width):v.h(j)
        bv=prepare(v)
        check(all(r.status=="PASS" for r in bv.verify(*(StateEigen((0,1<<j,int(bit))) for j,bit in enumerate(reversed(bits))))))
    for bad_c in (QuantumCircuit(1,1),QuantumCircuit(1,global_phase=.125)):
        reject(lambda:prepare(bad_c))
    rot=QuantumCircuit(1);rot.rx(.2,0);reject(lambda:prepare(rot))
    from qiskit.circuit import Gate
    from qiskit.circuit.library import HGate
    class Spoof(Gate):
        @property
        def base_class(self):return HGate
    spoof=QuantumCircuit(1);spoof.append(Spoof("spoof_h",1,[]),[0])
    # Qiskit may convert the claimed base class to its native standard
    # representation during append. Test the actual stored instruction:
    # reject a surviving custom type; if canonicalized, verify its
    # resulting H semantics against Qiskit, not the pre-insertion object.
    stored=spoof.data[0].operation
    if type(stored) in (HGate,type(HGate())) and spoof.data[0].is_standard_gate():
        from qiskit.quantum_info import Operator
        assert Operator(spoof).equiv(Operator(HGate()))
        check(prepare(spoof).check(Contract(requires=Pauli("Z"),ensures=Pauli("X"))).passed)
    else:reject(lambda:prepare(spoof))
    custom=QuantumCircuit(1)
    custom.append(Gate("h",1,[]),[0])
    check(not custom.data[0].is_standard_gate())
    reject(lambda:prepare(custom))
    opened=QuantumCircuit(2);opened.cx(0,1,ctrl_state=0)
    reject(lambda:prepare(opened))
    # Standard singleton and canonical mutable gates remain admissible.
    mutable=QuantumCircuit(1);mutable.append(HGate().to_mutable(),[0])
    check(prepare(mutable).check(Contract(requires=Pauli("Z"),ensures=Pauli("X"))).passed)
    check(p.check(good).require().passed)
    try:p.check(bad).require()
    except AssertionError:checks+=1
    else:raise AssertionError("failed contract require accepted")
    reject(lambda:p.verify());reject(lambda:p.check(Contract(requires=(True,0,0),ensures=x)))
    reject(lambda:p.check(good,max_work=True))
    try:md.version("ketary-native-research")
    except md.PackageNotFoundError:checks+=1
    else:raise AssertionError("historical native distribution installed")
    check("qcontract_native_alpha" in sys.modules and "ketary_native_research" not in sys.modules)
    check("ketary" not in sys.modules and "benchmark" not in sys.modules and "native9" not in sys.modules)
    print(json.dumps({"checks":checks,"distribution":md.version("qcontract-alpha-local"),"native":md.version("qcontract-native-alpha-local"),"qiskit":md.version("qiskit"),"scope":"isolated installed wheels, ten admitted families, GHZ through 64, Bernstein-Vazirani, immutable snapshot, replay and invalid requests"},indent=2))
if __name__=="__main__":main()
