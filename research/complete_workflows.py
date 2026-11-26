"""Authored end-to-end pre-alpha workloads, not a human usability study."""
import json
import math
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

def bv():
    secret="1011"
    n=len(secret)
    c=q.Circuit(n+1)
    inputs=c.register("inputs",range(n))
    target=c.register("target",[n])
    c.x(target).h(inputs).h(target)
    c.apply(q.parity_oracle(secret),wires=(*inputs,*target)).h(inputs)
    native=QuantumCircuit(n+1)
    native.x(n)
    native.h(range(n+1))
    for i,bit in enumerate(reversed(secret)):
        if bit=="1":
            native.cx(i,n)
    native.h(range(n))
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(native).data,atol=1e-12,rtol=0)
    result=q.decode_bernstein_vazirani(c.run())
    assert result["status"]=="PASS" and result["label"]==secret
    assert abs(result["peak_probability"]-1)<1e-12
    return {"label":result["label"],"full_operator_match":True}

def qpe():
    precision=4
    phase=5/16
    c=q.Circuit(precision+1)
    counting=c.register("counting",range(precision))
    eigenstate=c.register("eigenstate",[precision])
    c.x(eigenstate).h(counting)
    for i,w in enumerate(counting):
        c.cp(2*math.pi*((phase*2**i)%1),w,eigenstate[0])
    c.apply(q.qft(precision,inverse=True),wires=counting)
    r=c.run()
    expected=np.zeros(1<<(precision+1),dtype=complex)
    expected[(1<<precision)+5]=1
    np.testing.assert_allclose(r.math.statevector(),expected,atol=1e-12,rtol=0)
    report=q.decode_phase_estimation(r,precision=precision)
    assert report["phase"]==phase
    return {"phase":report["phase"],"peak_probability":report["peak_probability"]}

def grover():
    c=q.grover("101",iterations=2)
    r=c.run()
    expected=math.sin(5*math.asin(1/math.sqrt(8)))**2
    r.test.probability("101",expected).require()
    assert max(r.math.probabilities(),key=r.math.probabilities().get)=="101"
    return {"marked":"101","probability":r.math.probability("101")}

def simon():
    secret="101"
    r=q.simon(secret).run()
    wires=range(len(secret)-1,-1,-1)
    probabilities=r.math.marginal_probabilities(wires)
    for label,p in probabilities.items():
        expected=0.25 if (int(label,2)&int(secret,2)).bit_count()%2==0 else 0
        assert abs(p-expected)<1e-12
    # Deterministic support oracle, then a separate seeded sample path.
    support=[label for label,p in probabilities.items() if p>1e-12]
    assert q.recover_simon(support,len(secret))==secret
    counts=r.sample(shots=64,seed=42,wires=wires)
    assert q.recover_simon(counts,len(secret))==secret
    return {"secret":secret,"support":support,"sampled_distinct":len(counts)}

def variational_sweep():
    theta=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(theta,0).cx(0,1)
    angles=[0,math.pi/4,math.pi/2,math.pi]
    plan=c.sweep(theta=angles)
    rows=[]
    for angle,result in zip(angles,plan.run(),strict=True):
        expected=math.cos(angle)
        actual=result.math.expectation({0:"Z"})
        assert abs(actual-expected)<1e-12
        assert abs(result.math.expectation("ZZ")-1)<1e-12
        rows.append({"theta":angle,"expectation":actual})
    return {"rows":rows}

def diagnose():
    ref=q.Circuit(4)
    pair=ref.register("pair",[0,2])
    ref.apply(q.bell(),wires=pair).checkpoint("prepared")
    observed=ref.copy().z(pair[0]).checkpoint("after")
    contract=observed.contract(expectations={"IXIX":1})
    checkpoints=observed.debug.verify_checkpoints({"prepared":contract,"after":contract})
    assert checkpoints.status=="FAIL" and checkpoints["first_nonpass"]==3
    comparison=observed.test.compare(ref,inputs=["0000"])
    assert comparison.status=="FAIL"
    evidence=comparison.evidence
    assert evidence is not None and evidence.reproduce()["reproduced"]
    assert ref.diff(observed).operator.status=="FAIL"
    return {"first_nonpass":checkpoints["first_nonpass"],"witness_reproduced":True}

def run():
    cases={fn.__name__:fn() for fn in (bv,qpe,grover,simon,variational_sweep,diagnose)}
    return {"scope":"six authored end-to-end workloads; mathematical/native oracles, no user productivity claim",
            "passed":len(cases),"cases":cases}

if __name__=="__main__":
    print(json.dumps(run(),indent=2,allow_nan=False))
