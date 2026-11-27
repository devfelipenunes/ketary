"""B6: analyze raw benchmark samples without claiming controlled hardware.

Use only rows with matched outputs and decisive statuses. The bootstrap
interval describes resampling of observed timings, not all-host uncertainty.
"""
import json,random,statistics,sys,math,pathlib
def ratio_interval(a,b,*,seed=6101,resamples=2000):
    if not a or not b or not all(math.isfinite(x) and x>0 for x in a+b):raise ValueError("positive finite samples")
    rng=random.Random(seed)
    ratios=sorted(statistics.median(rng.choices(b,k=len(b)))/statistics.median(rng.choices(a,k=len(a))) for _ in range(resamples))
    return {"ratio":statistics.median(b)/statistics.median(a),"resample_low":ratios[int(resamples*.025)],"resample_high":ratios[int(resamples*.975)-1],"samples":[len(a),len(b)]}
def main():
    data=json.loads(pathlib.Path(sys.argv[1]).read_text());ours,theirs=sys.argv[2:4]
    rows=[];excluded=[]
    for r in data["rows"]:
        identity={k:v for k,v in r.items() if k not in ("timings","setup","results","values")}
        t=r["timings"]
        if ours not in t or theirs not in t:excluded.append({"row":identity,"reason":"unavailable baseline"});continue
        # Refuse to infer speed superiority if the exact route did not resolve.
        statuses=r.get("statuses",[])+([r["status"]] if "status" in r else [])+[v["native"] for v in r.get("results",[]) if "native" in v]
        if any(s not in ("PASS","FAIL") for s in statuses) or any(r.get(k,r.get("queries",0))<r.get("queries",0) for k in ("default_decisive","dag_decisive")):
            excluded.append({"row":identity,"reason":"incomplete decisive coverage"});continue
        rows.append({"row":identity,**ratio_interval(t[ours]["samples_ms"],t[theirs]["samples_ms"])})
    print(json.dumps({"comparison":[ours,theirs],"matched_rows":len(rows),"median_ratio":statistics.median(x["ratio"] for x in rows) if rows else None,
                      "wins":sum(x["ratio"]>1 for x in rows),"losses":sum(x["ratio"]<1 for x in rows),"excluded":excluded,"rows":rows,
                      "scope":"observational shared-host sample bootstrap, not controlled or cross-host certification; caller must ensure outputs match"},indent=2,allow_nan=False))
if __name__=="__main__":main()
