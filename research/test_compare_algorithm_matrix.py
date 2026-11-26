"""Regression tests for the BENCH04 report integrity gate (stdlib only)."""
import copy
import statistics
import unittest
from compare_algorithm_matrix import compare, percentile, validate


def report():
    raw=[1.0,2.0,3.0]
    median=statistics.median(raw)
    sample={"raw_ms":raw,"median_ms":median,"p95_ms":percentile(raw,.95),
            "p99_ms":percentile(raw,.99),"min_ms":min(raw),"max_ms":max(raw),
            "mean_ms":statistics.mean(raw),"stdev_ms":statistics.stdev(raw),
            "mad_ms":statistics.median(abs(x-median) for x in raw)}
    row={"name":"ghz","stage":"execute_original","input":"zero","n":4,
         "original_gates":4,"original_depth":4,"original_two_plus":3,
         "gate_histogram":{"h":1,"cx":3},"state_bytes":256,"family":"ghz",
         "samples":{"native":copy.deepcopy(sample),"ketary":copy.deepcopy(sample)},
         "validation":{"native":"checked","ketary":"checked"},
         "paired_ratio_to_native":{"native":{"median":1.0,"p95":1.0},
                                   "ketary":{"median":1.0,"p95":1.0}},
         "orders":[["native","ketary"],["ketary","native"],["native","ketary"]]}
    return {"seed":1101,"suite":"algorithms","repetitions":3,"python":"3.12",
            "qiskit":"2.6.2","aer":"0.18.4","numpy":"2","platform":"Linux",
            "affinity":[0,1],"rows":[row],"excluded":[]}


class EvidenceTests(unittest.TestCase):
    def test_valid(self):
        before=report()
        self.assertEqual(len(compare(before,copy.deepcopy(before))),2)

    def test_reject_invalid_samples(self):
        for values in ([0,2,3],[float("nan"),2,3],[True,2,3],[1,2],[-1,2,3]):
            with self.subTest(values=values):
                data=report()
                data["rows"][0]["samples"]["ketary"]["raw_ms"]=values
                with self.assertRaises(ValueError):
                    validate(data)

    def test_reject_inconsistent_statistics(self):
        for field in ("median_ms","p95_ms","p99_ms","mean_ms","stdev_ms","mad_ms","min_ms","max_ms"):
            with self.subTest(field=field):
                data=report()
                data["rows"][0]["samples"]["ketary"][field]+=1
                with self.assertRaises(ValueError):
                    validate(data)

    def test_reject_inconsistent_ratio(self):
        data=report()
        data["rows"][0]["paired_ratio_to_native"]["ketary"]["median"]=2
        with self.assertRaises(ValueError):
            validate(data)

    def test_reject_incomplete_validation_or_order(self):
        for field in ("validation","orders","paired_ratio_to_native"):
            with self.subTest(field=field):
                data=report()
                data["rows"][0][field].pop() if field=="orders" else data["rows"][0][field].pop("ketary")
                with self.assertRaises(ValueError):
                    validate(data)

    def test_reject_host_and_version_mismatch(self):
        for field,value in (("affinity",[2,3]),("python","3.13"),("platform","Other"),("qiskit","3")):
            with self.subTest(field=field):
                before=report()
                after=copy.deepcopy(before)
                after[field]=value
                with self.assertRaises(ValueError):
                    compare(before,after)

    def test_reject_changed_provenance(self):
        for field,value in (("source_blob","another"),("removed",{"measure":1}),
                            ("sdk_import_path","translated"),("state_bytes",128),
                            ("original_two_plus",2),("family","other")):
            with self.subTest(field=field):
                before=report()
                after=copy.deepcopy(before)
                after["rows"][0][field]=value
                with self.assertRaises(ValueError):
                    compare(before,after)

    def test_reject_missing_duplicate_and_unexpected_cases(self):
        before=report()
        for mode in ("missing","duplicate","unexpected"):
            with self.subTest(mode=mode):
                after=copy.deepcopy(before)
                if mode=="missing":
                    after["rows"].clear()
                else:
                    row=copy.deepcopy(after["rows"][0])
                    if mode=="unexpected":
                        row["name"]="not_in_baseline"
                    after["rows"].append(row)
                with self.assertRaises(ValueError):
                    compare(before,after)

    def test_allow_explicit_candidate_only_stage(self):
        before=report()
        after=copy.deepcopy(before)
        row=copy.deepcopy(after["rows"][0])
        row["stage"]="execute_common_basis"
        after["rows"].append(row)
        self.assertEqual(len(compare(before,after)),4)


if __name__=="__main__":
    unittest.main()
