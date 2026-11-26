"""I07/I08/I10: public study rehearsal, strict manifests, paired analysis.

A public calibration packet is never an independent held-out study.
Private task families must be authored and evaluated separately.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import random
from statistics import mean
from corpus_v03 import CASES,FRAMEWORKS
from ketary_eval_v03 import grade_packet,export


def assignment(arm,seed=42):
    """Balanced ordering, not recruitment or random assignment of real people."""
    if type(arm) is not int or not 0<=arm<6:
        raise ValueError("arm 0..5")
    order=list(FRAMEWORKS)
    if arm>=3:
        order.reverse()
    k=arm%3
    order=order[k:]+order[:k]
    families=sorted({(c["kind"],c["family"]) for c in CASES})
    random.Random(seed).shuffle(families)
    # Family-level separation prevents repeated analogous tasks in a session.
    groups=[set(families[i::3]) for i in range(3)]
    return [{"framework":framework,"condition":"card","tasks":[p for p in export(framework,"card",seed)
            if (next(c for c in CASES if c["id"]==p["id"])["kind"],
                next(c for c in CASES if c["id"]==p["id"])["family"]) in group]}
            for framework,group in zip(order,groups,strict=True)]


def evaluate_run(manifest):
    required={"study","participant","replicate","model_version","framework","condition","responses"}
    if type(manifest) is not dict or set(manifest)!=required:
        raise ValueError("invalid manifest fields")
    if manifest["study"] not in ("human","agent"):
        raise ValueError("study must be human or agent")
    if type(manifest["participant"]) is not str or not manifest["participant"]:
        raise ValueError("pseudonymous participant required")
    if type(manifest["replicate"]) is not int or manifest["replicate"]<0:
        raise ValueError("invalid replicate")
    if manifest["study"]=="agent" and (type(manifest["model_version"]) is not str or not manifest["model_version"]):
        raise ValueError("agent model version required")
    if manifest["study"]=="human" and manifest["model_version"] is not None:
        raise ValueError("human data must not specify a model")
    responses=manifest["responses"]
    if type(responses) is not list:
        raise ValueError("response records required")
    rows=[]
    metrics={}
    for record in responses:
        if type(record) is not dict or set(record)!={"id","response","elapsed_ms","input_tokens","output_tokens","tool_calls","repair_rounds"}:
            raise ValueError("invalid response metrics")
        if type(record["id"]) is not str:
            raise ValueError("invalid task ID")
        for key in ("elapsed_ms","tool_calls","repair_rounds"):
            if type(record[key]) is not int or record[key]<0:
                raise ValueError("nonnegative integer metrics required")
        for key in ("input_tokens","output_tokens"):
            value=record[key]
            if manifest["study"]=="human":
                if value is not None:
                    raise ValueError("human token metrics must be null")
            elif type(value) is not int or value<0:
                raise ValueError("actual provider tokens required")
        rows.append({"id":record["id"],"response":record["response"]})
        metrics[record["id"]]={k:record[k] for k in ("elapsed_ms","input_tokens","output_tokens","tool_calls","repair_rounds")}
    result=grade_packet({"framework":manifest["framework"],"condition":manifest["condition"],"responses":rows})
    return {"study":manifest["study"],"participant":manifest["participant"],"replicate":manifest["replicate"],
            "model_version":manifest["model_version"],"framework":manifest["framework"],"condition":manifest["condition"],
            "corpus":"public-v03-calibration","n":result["n"],"pass":result["pass"],
            "rows":[dict(row,metrics=metrics.get(row["id"])) for row in result["rows"]]}


def paired_summary(runs,*,seed=42,repeats=2000):
    """Pair complete public packets within participant/replicate/condition.

    Cluster bootstrap by participant over complete pairs; descriptive only.
    Missing responses are failures. Never pool humans with agents or models.
    """
    if not runs or type(repeats) is not int or not 100<=repeats<=10000:
        raise ValueError("invalid runs or repeat count")
    groups=defaultdict(dict)
    for run in runs:
        key=(run["study"],run["model_version"],run["condition"],run["participant"],run["replicate"])
        if run["framework"] in groups[key]:
            raise ValueError("duplicate run")
        groups[key][run["framework"]]=run
    strata=defaultdict(lambda:defaultdict(list))
    for key,arms in groups.items():
        if set(arms)!=set(FRAMEWORKS):
            raise ValueError("complete matched framework triplet required")
        for comparator in ("qiskit","ketary"):
            a,b=arms["candidate"],arms[comparator]
            if a["n"]!=180 or b["n"]!=180:
                raise ValueError("incomplete denominator")
            strata[(*key[:3],comparator)][key[3]].append((a["pass"]-b["pass"])/180)
    rng=random.Random(seed)
    out=[]
    for key,participants in sorted(strata.items(),key=lambda x:str(x[0])):
        values=[mean(v) for v in participants.values()]
        boot=sorted(mean(rng.choices(values,k=len(values))) for _ in range(repeats))
        out.append({"study":key[0],"model_version":key[1],"condition":key[2],"comparator":key[3],
                    "participant_clusters":len(values),"paired_replicates":sum(map(len,participants.values())),
                    "mean_pass_rate_difference":mean(values),
                    "descriptive_bootstrap_95": [boot[int(.025*repeats)],boot[int(.975*repeats)-1]] if len(values)>1 else None})
    return {"corpus":"public-v03-calibration","warning":"rehearsal only; no independent efficacy inference; family clustering remains for held-out study","comparisons":out}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--assignment",type=int)
    g.add_argument("--evaluate",type=Path)
    g.add_argument("--analyze",type=Path)
    args=p.parse_args()
    if args.assignment is not None:
        result=assignment(args.assignment)
    else:
        path=args.evaluate or args.analyze
        if path.stat().st_size>8*1024*1024:
            raise ValueError("input exceeds 8 MiB")
        data=json.loads(path.read_text(encoding="utf-8"))
        result=evaluate_run(data) if args.evaluate else paired_summary([evaluate_run(m) for m in data])
    print(json.dumps(result,indent=2,allow_nan=False))
