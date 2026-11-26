"""Two #298 planted defect and repair applications; evidence formats differ."""
import inspect,io,json,random,time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,qpy,transpile
from qiskit.quantum_info import Operator,Statevector
from research.circuit_rewrite_ladder import metrics,stats

def sdk_build(kind,wire):
    if kind=="phase":good=q.Circuit(3).h(0).cx(0,1).cx(1,2)
    else:
        block=q.Circuit(3).ccx(0,1,2).cx(2,0)
        good=block.copy().apply(block.inverse())
    return good,good.copy().z(wire)

def native_build(kind,wire):
    if kind=="phase":
        good=QuantumCircuit(3);good.h(0);good.cx(0,1);good.cx(1,2)
    else:
        block=QuantumCircuit(3);block.ccx(0,1,2);block.cx(2,0)
        good=block.compose(block.inverse())
    bad=good.copy();bad.z(wire)
    return good,bad

def sdk_verify(pair,kind,wire):
    good,bad=pair
    if kind=="phase":
        good.run().test.distribution(bad.run()).require()
        obs=q.X(0)@q.X(1)@q.X(2)
        assert good.run().math.expectation(obs)>1-1e-9 and bad.run().math.expectation(obs)<-1+1e-9
        label="000"
    else:
        assert bad.test.compare(good,inputs=["000"],complete=False).status=="INCONCLUSIVE"
        label="+++"
    assert bad.test.compare(good,inputs=[label],complete=True).status=="FAIL"
    report=bad.test.compare(good,inputs=[label],complete=False)
    assert report.status=="FAIL" and report.evidence is not None
    payload=report.evidence.to_json()
    assert q.Evidence.from_json(payload).reproduce()["reproduced"]
    bad.copy().z(wire).test.equivalent(good).require()
    return len(payload.encode("utf-8"))

def native_verify(pair,kind,wire):
    good,bad=pair
    if kind=="phase":
        a=Statevector.from_instruction(good).data;b=Statevector.from_instruction(bad).data
        np.testing.assert_allclose(abs(a)**2,abs(b)**2,atol=1e-9,rtol=0)
        np.testing.assert_allclose([np.vdot(a,a[::-1]),np.vdot(b,b[::-1])],[1,-1],atol=1e-9,rtol=0)
        label="000"
    else:
        z=Statevector.from_label("000")
        np.testing.assert_allclose(z.evolve(good).data,z.evolve(bad).data,atol=1e-9,rtol=0)
        label="+++"
    assert np.max(abs(Operator(good).data-Operator(bad).data))>1e-9
    v=Statevector.from_label(label)
    assert np.linalg.norm(v.evolve(good).data-v.evolve(bad).data)>1e-9
    stream=io.BytesIO();qpy.dump([good,bad],stream);size=stream.tell();stream.seek(0)
    a,b=qpy.load(stream)
    assert np.linalg.norm(v.evolve(a).data-v.evolve(b).data)>1e-9
    repaired=bad.copy();repaired.z(wire)
    np.testing.assert_allclose(Operator(repaired).data,Operator(good).data,atol=1e-9,rtol=0)
    return size

def evaluate(kind,wire,seed,reps=3):
    routes={"ketary":(sdk_build,sdk_verify),"qiskit":(native_build,native_verify)}
    rng=random.Random(seed);out={}
    expected=np.diag([(-1)**((i>>wire)&1) for i in range(8)])
    for key,(build,verify) in routes.items():
        pair=build(kind,wire)
        good,bad=[c.to_qiskit() if key=="ketary" else c for c in pair]
        a,b=Operator(good).data,Operator(bad).data
        np.testing.assert_allclose(b,expected@a,atol=1e-9,rtol=0)
        if kind=="reversible":np.testing.assert_allclose(a,np.eye(8),atol=1e-9,rtol=0)
        lowered=transpile(bad,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
        np.testing.assert_allclose(Operator(lowered).data,b,atol=1e-9,rtol=0)
        source=inspect.getsource(build)+"\n"+inspect.getsource(verify)
        out[key]=dict(source=source,metrics=metrics(source),common_gates=len(lowered.data),common_depth=lowered.depth(),build=[],verify=[],payload_bytes=[])
    for _ in range(reps):
        for key in rng.sample(list(routes),2):
            build,verify=routes[key];t=time.perf_counter_ns();pair=build(kind,wire);b=time.perf_counter_ns()
            size=verify(pair,kind,wire);e=time.perf_counter_ns()
            out[key]["build"].append((b-t)/1e6);out[key]["verify"].append((e-b)/1e6)
            out[key]["payload_bytes"].append(size)
    for row in out.values():
        for k in ("build","verify"):row[k]=stats(row[k])
    return dict(kind=kind,wire=wire,seed=seed,paths=out)

def run(reps=3):
    return [evaluate(kind,wire,seed,reps) for seed in (1101,2202,3303) for kind in ("phase","reversible") for wire in (0,2)]

if __name__=="__main__":
    print(json.dumps({"scope":"same planted defect, repaired strict operator and reproduced selected witness; typed JSON evidence vs native QPY plus caller-managed witness; distinct payload guarantees","rows":run()},indent=2,allow_nan=False))
