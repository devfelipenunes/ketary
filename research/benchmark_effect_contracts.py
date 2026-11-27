"""Diagnostic end-to-end benchmarks with the installed Ketary SDK.

No performance assertions, no runtime or public API changes.
"""
import json
import platform
import time
import random
import statistics
import importlib.metadata
import os

import numpy as np
import ketary as q
from qiskit.quantum_info import Operator
from effect_contracts import verify_circuit, verify_effect, projector

REPS = 31
WARMUPS = 4
SEED = 20261126


def summarize(values):
    return {"median_ms": statistics.median(values), "p95_ms": float(np.percentile(values, 95)),
            "samples_ms": values}


def measure(methods, rng):
    for _ in range(WARMUPS):
        for f in methods.values():
            f()
    raw = {k: [] for k in methods}
    names = list(methods)
    for _ in range(REPS):
        rng.shuffle(names)
        for name in names:
            start = time.perf_counter_ns()
            methods[name]()
            raw[name].append((time.perf_counter_ns() - start)/1e6)
    return {k: summarize(v) for k,v in raw.items()}


def ghz(n, bad=False):
    c = q.Circuit(n).h(0)
    for i in range(1,n):
        c.cx(0,i)
    if bad:
        c.z(0)
    return c


def oracle(n, pairs, bad=False):
    c = q.Circuit(n)
    for _ in range(pairs):
        c.cx(0,n-1).cx(1,n-1).z(n-1).cx(1,n-1).cx(0,n-1)
    if bad:
        c.cx(0,n-1)
    return c


def effect_methods(build, pre, post, expected, rng):
    c = build()
    native = c.to_qiskit()
    u = Operator(native).data
    r = verify_circuit(c,pre,post)
    a = verify_effect(pre,post,(u,))
    # Identical full numerical criterion and witness-producing path.
    assert r.status == a.status == expected
    assert r.specification_sha256 == a.specification_sha256
    assert r.channel_sha256 == a.channel_sha256
    if expected == "FAIL":
        assert r.witness is not None
        v = np.array([complex(*p) for p in r.witness])
        gap = float(np.vdot(v,pre@v).real-np.vdot(u@v,post@(u@v)).real)
        assert gap > r.atol
        assert abs(gap-r.witness_gap)<1e-9
    methods = {
        "build": build,
        "ketary_run": c.run,
        "native_export": c.to_qiskit,
        "native_operator": lambda: Operator(native).data,
        "effect_on_prebuilt_operator": lambda: verify_effect(pre,post,(u,)),
        "native_operator_and_effect": lambda: verify_effect(pre,post,(Operator(native).data,)),
        "ketary_effect_verify": lambda: verify_circuit(c,pre,post),
        "ketary_build_and_effect_verify": lambda: verify_circuit(build(),pre,post),
        "report_to_dict": r.to_dict,
    }
    return {"status": r.status, "max_residual": r.max_residual, "witness_gap":r.witness_gap,
            "gates": len(native.data), "timings":measure(methods,rng)}


def snapshot(n,bad,rng):
    c = ghz(n,bad)
    contract = q.Contract(n, probabilities={"0"*n:.5,"1"*n:.5},
                          expectations={"X"*n:1})
    r = c.run()
    expected = "FAIL" if bad else "PASS"
    assert contract.verify(r).status == expected
    # Same existing SDK snapshot predicates on the same result, without grouping.
    def separate_checks():
        checks = (r.test.probability("0"*n,.5),r.test.probability("1"*n,.5),
                  r.test.expectation("X"*n,1))
        return checks
    assert ("FAIL" if any(x.status=="FAIL" for x in separate_checks()) else "PASS") == expected
    return {"status":expected,"gates":len(c.to_qiskit().data),
            "timings":measure({
                "ketary_build": lambda: ghz(n,bad),
                "ketary_run": c.run,
                "snapshot_verify":lambda:contract.verify(r),
                "separate_snapshot_checks":separate_checks,
                "ketary_run_and_snapshot_verify":lambda:contract.verify(c.run()),
                "ketary_build_run_verify":lambda:contract.verify(ghz(n,bad).run()),
            },rng)}


def main():
    rng=random.Random(SEED)
    rows=[]
    for n in (2,3,4,5,8,12,16):
        for bad in (False,True):
            rows.append({"family":"ghz_snapshot","qubits":n,"mutant":bad,**snapshot(n,bad,rng)})
    for n in (2,3,4,5):
        zero=np.eye(1<<n,dtype=complex)[:,0]
        plus=zero.copy()/np.sqrt(2)
        plus[-1]=1/np.sqrt(2)
        pre,post=projector(zero),projector(plus)
        for bad in (False,True):
            rows.append({"family":"ghz_effect","qubits":n,"mutant":bad,
                         **effect_methods(lambda:ghz(n,bad),pre,post,"FAIL" if bad else "PASS",rng)})
    for n in (3,4,5):
        p=np.diag(np.r_[np.ones(1<<(n-1)),np.zeros(1<<(n-1))]).astype(complex)
        for pairs in (1,8,32):
            for bad in (False,True):
                rows.append({"family":"oracle_clean_ancilla","qubits":n,"repetitions":pairs,
                             "mutant":bad,**effect_methods(lambda:oracle(n,pairs,bad),p,p,
                                                           "FAIL" if bad else "PASS",rng)})
    out={"schema":1,"seed":SEED,"repetitions":REPS,"warmups":WARMUPS,
         "python":platform.python_version(),"platform":platform.platform(),
         "versions":{k:importlib.metadata.version(k) for k in ("ketary","qiskit","numpy")},
         "threads":{k:os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS")},
         "scope":"diagnostic shared CI, warm process; full effect path includes admission, export, operator, hashes, witness; no hardware or formal proof",
         "rows":rows}
    print(json.dumps(out,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
