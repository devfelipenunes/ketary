"""KetaryEval v0.3: public calibration, bounded semantic grading and export.

Run from any working directory. No submitted Python is executed and no model
API is contacted. The legacy v0.2 entry point and metrics remain unchanged.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import random

import numpy as np
from qiskit.quantum_info import Statevector
from corpus_v03 import CASES, FRAMEWORKS, TARGET, source_for
from ketary_eval import grade as legacy_grade, native, prompt as legacy_prompt, reference
from source_reader import read_source


def prompt(case, framework, condition="card"):
    p=legacy_prompt(case,framework,condition)
    if "suffix" in case:
        p["source"]=source_for(case,framework)
    if "max_count" in case:
        p["constraints"]+=f" Maximum gate count: {case['max_count']}."
    if case["kind"]=="testing":
        p["response_schema"]={"answer":["input bit string","expected output bit string"]}
    return p


def _result(status,reason):
    return {"status":status,"reason":reason}


def grade(case,framework,response):
    if framework not in FRAMEWORKS:
        return _result("INVALID","unknown framework")
    if case["kind"]=="testing":
        if type(response) is not dict or set(response)!={"answer"}:
            return _result("INVALID","answer schema")
        answer=response["answer"]
        n=case["n"]
        if (type(answer) is not list or len(answer)!=2 or
            any(type(s) is not str or len(s)!=n or set(s)-{"0","1"} for s in answer)):
            return _result("INVALID","expected two fixed-width binary strings")
        initial=Statevector.from_label(answer[0])
        target=int(answer[1],2)
        good=initial.evolve(native(n,case["intended"])).probabilities()[target]
        bad=initial.evolve(native(n,case["source"])).probabilities()[target]
        kills=bool(np.isclose(good,1,atol=1e-9,rtol=0) and not np.isclose(bad,1,atol=1e-9,rtol=0))
        return _result("PASS" if kills else "FAIL","test passes intended operator and kills mutant")
    verdict=legacy_grade(case,framework,response)
    if verdict["status"]=="PASS" and "max_count" in case:
        parsed=read_source(response["code"])
        if len(parsed["operations"])>case["max_count"]:
            return _result("FAIL","operator equivalent but exceeds gate budget")
    return verdict


def self_test():
    rows=[]
    for case in CASES:
        for framework in FRAMEWORKS:
            good=grade(case,framework,reference(case,framework))
            bad=grade(case,framework,reference(case,framework,True))
            assert good["status"]=="PASS",(case["id"],framework,good)
            assert bad["status"]=="FAIL",(case["id"],framework,bad)
            rows.append({"id":case["id"],"framework":framework})
    return {"cases":len(CASES),"categories":dict(Counter(c["kind"] for c in CASES)),
            "reference_pass":len(rows),"mutants_rejected":len(rows),
            "families":len({(c["kind"],c["family"]) for c in CASES}),
            "note":"public authored and parameterized calibration; not independent model outcomes"}


def export(framework,condition,seed):
    rows=[prompt(c,framework,condition) for c in CASES]
    random.Random(seed).shuffle(rows)
    return rows


def grade_packet(rows):
    """Grade exactly one complete API packet; missing responses count as failures.

    The caller supplies a framework and documentation condition, then a list
    of task responses. Duplicate and unknown IDs are rejected, not averaged.
    """
    if type(rows) is not dict or set(rows)!={"framework","condition","responses"}:
        raise ValueError("expected framework, condition, responses")
    framework,condition=rows["framework"],rows["condition"]
    if framework not in FRAMEWORKS or condition not in ("none","card","reference"):
        raise ValueError("invalid packet condition")
    responses=rows["responses"]
    if type(responses) is not list or len(responses)>len(CASES):
        raise ValueError("invalid response list")
    by_id={c["id"]:c for c in CASES}
    submitted={}
    for row in responses:
        if type(row) is not dict or set(row)!={"id","response"}:
            raise ValueError("invalid response row")
        cid=row["id"]
        if type(cid) is not str or cid not in by_id or cid in submitted:
            raise ValueError("unknown or duplicate task ID")
        submitted[cid]=row["response"]
    results=[]
    for case in CASES:
        cid=case["id"]
        verdict=grade(case,framework,submitted[cid]) if cid in submitted else _result("MISSING","no response")
        results.append({"id":cid,"kind":case["kind"],"family":case["family"],**verdict})
    breakdown={}
    for kind,n in TARGET.items():
        counts=Counter(row["status"] for row in results if row["kind"]==kind)
        breakdown[kind]={"n":n,"pass":counts["PASS"],"statuses":dict(counts)}
    abstention={}
    for expected in ("PASS","UNSUPPORTED"):
        ids={c["id"] for c in CASES if c["kind"]=="abstention" and c["answer"]==expected}
        abstention[expected]={"n":len(ids),"correct":sum(row["status"]=="PASS" for row in results if row["id"] in ids)}
    return {"framework":framework,"condition":condition,"n":len(CASES),
            "pass":sum(row["status"]=="PASS" for row in results),
            "by_kind":breakdown,"abstention":abstention,"rows":results}


def main():
    parser=argparse.ArgumentParser()
    options=parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--self-test",action="store_true")
    options.add_argument("--prompts",choices=FRAMEWORKS)
    options.add_argument("--grade",type=Path)
    parser.add_argument("--condition",choices=("none","card","reference"),default="card")
    parser.add_argument("--seed",type=int,default=42)
    args=parser.parse_args()
    if args.self_test:
        output=self_test()
    elif args.prompts:
        output=export(args.prompts,args.condition,args.seed)
    else:
        if args.grade.stat().st_size>2*1024*1024:
            raise ValueError("response packet exceeds 2 MiB")
        output=grade_packet(json.loads(args.grade.read_text(encoding="utf-8")))
    print(json.dumps(output,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
