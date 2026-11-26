"""Independently written small adaptations of published developer reports.

Not original historical programs; not an unbiased or held-out sample.
Expected outputs use elementary mathematical oracles, not Ketary verdicts.
"""
import json
import numpy as np
import ketary as q
from math import pi

def cases():
    # SO 63283443: reversed bit conventions.
    yield ("bit-order","https://stackoverflow.com/questions/63283443",
           q.Circuit(3).x(2),q.Circuit(3).x(0),"000")
    # Same report: accidentally accumulating gates rather than fresh circuits.
    yield ("builder-reuse","https://stackoverflow.com/questions/63283443",
           q.Circuit(3).x(0).ccx(0,1,2).x(1).ccx(0,1,2),
           q.Circuit(3).x(1).ccx(0,1,2),"000")
    # SO 62661255: H on target rather than X produces uniform superposition.
    yield ("bell-preparation","https://stackoverflow.com/questions/62661255",
           q.Circuit(2).h(0).h(1).cx(0,1),
           q.Circuit(2).h(0).x(1).cx(0,1),"00")
    # SO 63342432: distinguish forward and inverse Fourier sign.
    yield ("fourier-direction","https://stackoverflow.com/questions/63342432",
           q.qft(3,inverse=True),q.qft(3),"001")
    # QCSE 9871: ancilla must be returned to zero.
    yield ("missing-uncompute","https://quantumcomputing.stackexchange.com/questions/9871",
           q.Circuit(5).ccx(0,1,3).ccx(2,3,4),
           q.Circuit(5).ccx(0,1,3).ccx(2,3,4).ccx(0,1,3),"00111")
    # Qiskit 5580: control mapped to wrong wire during embedding.
    small=q.Circuit(3).crz(pi/2,2,0).crz(pi/4,2,1)
    yield ("controlled-wire-mapping","https://github.com/Qiskit/qiskit/issues/5580",
           q.Circuit(4).compose(small,wires=[0,2,3]),
           q.Circuit(4).compose(small,wires=[2,3,0]),"0001")

def run():
    rows=[]
    for name,source,a,b,label in cases():
        from qiskit.quantum_info import Operator,Statevector
        init=Statevector.from_label(label).data
        delta=(Operator(a.to_qiskit()).data-Operator(b.to_qiskit()).data)@init
        distance=float(np.linalg.norm(delta))
        assert distance>1e-9, name
        report=a.test.compare(b,inputs=[label],complete=False)
        assert report["status"]=="FAIL",name
        artifact=q.Evidence.from_json(json.dumps(report["evidence"]))
        replay=artifact.reproduce()
        assert replay["reproduced"]
        assert abs(distance-replay["state_l2"])<1e-9
        control=b.test.compare(b.copy(),inputs=[label])
        assert control["status"]=="PASS",name
        rows.append({"case":name,"source":source,"input":label,"oracle_l2":distance,
                     "detected":True,"reproduced":True,"positive_control":True})
    return {"scope":"six public-report adaptations; not full Bugs4Q reproduction",
            "cases":rows,"detected":len(rows),"reproduced":len(rows),"controls":len(rows)}

if __name__=="__main__":
    print(json.dumps(run(),indent=2,allow_nan=False))
