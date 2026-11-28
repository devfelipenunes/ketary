"""Design review: choose the correct scope, not the strongest assertion."""
import json
import pathlib
import sys
import numpy as np
import qcontract
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qcontract import Named, Plan, clean_ancillas, prepare

def main():
    assert sys.flags.isolated
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())
    reference = QuantumCircuit(2)
    ref = prepare(reference)
    cases = (
        ("uncompute", (("cx",0,1),("cx",0,1)), ("PASS","PASS","PASS")),
        ("missing uncompute", (("cx",0,1),), ("FAIL","FAIL","FAIL")),
        ("logical Z", (("z",0),), ("PASS","FAIL","FAIL")),
        ("workspace Z", (("z",1),), ("PASS","PASS","FAIL")),
        ("workspace X", (("x",1),), ("FAIL","FAIL","FAIL")),
        ("logical X", (("x",0),), ("PASS","FAIL","FAIL")),
        ("identity pair", (("h",0),("h",0)), ("PASS","PASS","PASS")),
    )
    rows = []
    for name, gates, expected in cases:
        circuit = QuantumCircuit(2)
        for gate, *wires in gates:
            getattr(circuit, gate)(*wires)
        engine = prepare(circuit)
        plan = Plan((
            clean_ancillas("Workspace initially and finally clean", wires=(1,)),
            Named("Logical identity on clean subspace", engine.action_matches(ref, ancillas=(1,))),
            Named("Strict whole-register identity", engine.equivalent_to(ref, strict=True)),
        ))
        outcome = plan.verify(engine)
        observed = tuple(r.status for _,r in outcome.results)
        u = Operator(circuit).data
        clean = np.allclose(u[2:,:2],0,rtol=0,atol=1e-12)
        # A single common unit-modulus factor must apply to both input columns.
        phase = u[0,0]
        relative = np.isclose(abs(phase),1,rtol=0,atol=1e-12) and np.allclose(
            u[:,:2], phase*np.eye(4)[:,:2],rtol=0,atol=1e-12)
        strict = np.allclose(u,np.eye(4),rtol=0,atol=1e-12)
        oracle = tuple("PASS" if v else "FAIL" for v in (clean,relative,strict))
        assert observed == expected == oracle, (name,observed,expected,oracle)
        rows.append({"case":name,"expected":expected,"observed":observed,
                     "numeric_reference":oracle,"reports":outcome.explain()})
    print(json.dumps({"scope":"seven developer-authored scope selection cases; not general proof coverage",
                      "checks":3*len(rows),"cases":rows},indent=2,allow_nan=False))

if __name__=="__main__":
    main()
