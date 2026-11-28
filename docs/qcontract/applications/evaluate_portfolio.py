"""Application-driven exact scaling and diagnostic checks, not host benchmarks."""
import json
import pathlib
import sys
import time

import qcontract
from qiskit import QuantumCircuit
from qcontract import Plan, pauli_on, prepare, zero_input


def ghz_scaling():
    rows=[]
    for width in (4,8,16,32,64):
        claims=[zero_input("Global X",stabilizes=pauli_on(width,tuple((w,"X") for w in range(width))))]
        claims.extend(zero_input(f"Correlation 0:{w}",stabilizes=pauli_on(width,((0,"Z"),(w,"Z"))))
                      for w in range(1,width))
        plan=Plan(tuple(claims))
        for defect in ("none","phase","last_link"):
            c=QuantumCircuit(width)
            c.h(0)
            for w in range(1,width):
                if defect=="last_link" and w==width-1:continue
                c.cx(0,w)
            if defect=="phase":c.z(0)
            # Closed-form stabilizer predictions: the omitted last wire
            # remains |0>; the other wires form a smaller GHZ state.
            expected=(("PASS",)*width if defect=="none" else
                      ("FAIL",)+("PASS",)*(width-1) if defect=="phase" else
                      ("FAIL",)+("PASS",)*(width-2)+("FAIL",))
            start=time.perf_counter_ns()
            p=prepare(c)
            prepare_ns=time.perf_counter_ns()-start
            start=time.perf_counter_ns()
            outcome=plan.verify(p)
            verify_ns=time.perf_counter_ns()-start
            actual=tuple(r.status for _,r in outcome.results)
            assert actual==expected,(width,defect,actual,expected)
            assert p.statuses(*(o.specification for o in plan.obligations))==expected
            # Zero allocation per obligation is unresolved, not a refutation.
            bounded=plan.verify(p,max_work=1)
            assert all(r.status=="INCONCLUSIVE" for _,r in bounded.results)
            rows.append({"width":width,"gates":len(c.data),"defect":defect,
                         "obligations":width,"expected":expected,
                         "prepare_ns_diagnostic":prepare_ns,"verify_ns_diagnostic":verify_ns,
                         "reports":outcome.explain(),"bounded_reports":bounded.explain()})
    return {"cases":rows,"oracle":"analytic GHZ stabilizers; no dense statevector at large widths"}


def diagnostic_scope():
    # One all-input transition can survive a meaningful defect. An
    # independent second generator makes the single-qubit action complete
    # modulo global phase. Count concrete survivors, not inferred causes.
    from qcontract import transition
    first=transition("Z to X",before="Z",after="X")
    second=transition("X to Z",before="X",after="Z")
    full=Plan((first,second))
    rows=[]
    for case,gates,expected in (
        ("H",("h",),("PASS","PASS")),
        ("allowed HHH",("h","h","h"),("PASS","PASS")),
        ("X after H",("h","x"),("PASS","FAIL")),
        ("Z after H",("h","z"),("FAIL","PASS")),
        ("identity",(),("FAIL","FAIL")),
    ):
        c=QuantumCircuit(1)
        for gate in gates:getattr(c,gate)(0)
        p=prepare(c);outcome=full.verify(p)
        actual=tuple(r.status for _,r in outcome.results)
        assert actual==expected
        single=Plan((first,)).verify(p)
        assert single.results[0][1].status==expected[0]
        rows.append({"case":case,"single_pass":single.passed,"full_pass":outcome.passed,
                     "reports":outcome.explain()})
    defective=rows[2:]
    single_detected=sum(not row["single_pass"] for row in defective)
    full_detected=sum(not row["full_pass"] for row in defective)
    assert (single_detected,full_detected)==(2,3)
    return {"cases":rows,"true_defects":3,"single_detected":single_detected,
            "full_detected":full_detected,"allowed_variants":1,
            "boundary":"authored controls; report locates refuted property, not root cause"}


def main():
    assert sys.flags.isolated and qcontract.__version__=="0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())
    results={"ghz_scaling":ghz_scaling(),"diagnostic_scope":diagnostic_scope()}
    print(json.dumps({"scope":"analytic application scaling and diagnostic controls; shared CI timings exploratory",
                      "results":results},indent=2,allow_nan=False))


if __name__=="__main__":main()
