"""A small mathematical workflow: build, bind, verify and diagnose.

Run from an installed Python 3.12 environment:
    python examples/alpha_mathematical_workflow.py

The ideal-state model and checks are numerical; no hardware is used.
"""
from math import cos, sin
import ketary as q


def main():
    angle=q.Circuit.parameter("theta")
    layer=q.Circuit.symbolic(2).ry(angle,0).cx(0,1)
    circuit=q.Circuit.symbolic(4).apply_each(layer,placements=[(0,1),(2,3)])
    H=q.Z(0)+q.Z(2)+.4*(q.X(0)@q.X(1))
    values=[.2,.6,1.1]
    plan=circuit.sweep_rows((x,) for x in values)
    for x,result in zip(values,plan.run(),strict=True):
        expected=2*cos(x)+.4*sin(x)
        q.Contract(4,expectations={H:expected},normalized=True).verify(result).require()
        print(f"theta={x:.2f}, energy={result.math.expectation(H):.9f}")
    bound=circuit.bind({angle:values[1]})
    good=bound.run()
    defective=bound.copy().z(0)
    bad=defective.run()
    good.test.distribution(bad).require()
    expected=good.math.expectation(H)
    assert q.Contract(4,expectations={H:expected}).verify(bad).status=="FAIL"
    report=defective.test.compare(bound,inputs=["0000"])
    assert report.status=="FAIL" and report.evidence is not None
    assert report.evidence.reproduce()["reproduced"]
    print("Phase defect detected and witness reproduced.")


if __name__=="__main__":
    main()
