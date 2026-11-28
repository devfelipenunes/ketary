"""Run fourteen additional bounded algorithmic workloads on installed wheels."""
import json
import pathlib
import runpy
import sys

import qcontract

ROOT=pathlib.Path(__file__).resolve().parent
GROUPS={
    "fourier_search.py":("fourier","phase_estimation","grover","deutsch_jozsa"),
    "arithmetic_and_qec.py":("half_adder","incrementer","random_bit_preparation","five_qubit_code"),
    "advanced_workloads.py":("period_finding","quantum_walk","phase_kickback",
                             "syndrome_readout","conditional_router","reversible_comparator"),
}


def main():
    assert sys.flags.isolated
    assert qcontract.__version__=="0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    results={}
    for filename,names in GROUPS.items():
        scope=runpy.run_path(str(ROOT/filename))
        for name in names:
            assert name not in results
            results[name]=scope[name]()
    count=sum(len(result["cases"]) for result in results.values())
    assert len(results)==14 and count==103,(len(results),count)
    print(json.dumps({"scope":"bounded author-created algorithm suite",
                      "applications":len(results),"fixture_count":count,
                      "results":results},indent=2,allow_nan=False))


if __name__=="__main__":main()
