"""Five-minute installed-package workflow; no optional backend needed."""
import json
import ketary as q

def main():
    expected=q.Circuit(2).h(0).cx(0,1)
    observed=expected.copy().z(0)
    snapshot=observed.run()
    assert expected.run().test.distribution(snapshot).status=="PASS"
    contract=q.Contract(2,expectations={"XX":1,"ZZ":1})
    assert contract.verify(snapshot).status=="FAIL"
    report=observed.test.compare(expected,inputs=["00"])
    assert report["status"]=="FAIL"
    evidence=q.Evidence.from_json(json.dumps(report["evidence"]))
    assert evidence.reproduce()["reproduced"]
    fixed=expected.copy()
    contract.verify(fixed.run()).require()
    print("Equal probabilities can hide relative phase errors.")
    print(contract.verify(snapshot).render())
    print("Witness reproduced; corrected circuit verified.")

if __name__=="__main__":
    main()
