"""Canonical five-minute workflow; installed-package smoke test."""
import ketary as q

def main():
    expected = q.bell()
    observed = expected.copy().z(0)
    good, bad = expected.run(), observed.run()
    XX = q.X(0) @ q.X(1)
    contract = expected.contract(expectations={XX: 1, "ZZ": 1})
    contract.verify(good).require()
    good.test.distribution(bad).require()
    assert contract.verify(bad).status == "FAIL"
    report = observed.test.compare(expected, inputs=["00"])
    assert report.status == "FAIL"
    evidence = report.evidence
    assert evidence is not None and evidence.reproduce()["reproduced"]
    print("Equal probabilities can hide relative phase errors.")
    print(contract.verify(bad).render())
    print("Witness reproduced; corrected circuit verified.")

if __name__ == "__main__":
    main()
