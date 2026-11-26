"""Diagnostic measurement of bounded read context, no LLM token claims."""
import json
import random
import statistics
import time
import ketary as q

def encoded(obj):
    return len(json.dumps(obj,separators=(",",":"),allow_nan=False).encode("utf-8"))

def paired(a,b,reps=20):
    rng=random.Random(42)
    times=[[],[]]
    for f in (a,b):
        for _ in range(3): f()
    for _ in range(reps):
        order=[0,1];rng.shuffle(order)
        for i in order:
            start=time.perf_counter_ns(); (a,b)[i]();times[i].append((time.perf_counter_ns()-start)/1e6)
    return {"baseline_median_ms":statistics.median(times[0]),"candidate_median_ms":statistics.median(times[1]),
        "baseline_p95_ms":sorted(times[0])[18],"candidate_p95_ms":sorted(times[1])[18],
        "repetitions":reps}

def inspect_context():
    rows=[]
    for n in (32,1000,10000):
        c=q.Circuit(3)
        for i in range(n): c.h(i%3)
        def baseline():
            full=json.loads(c.to_json())
            return full["operations"][:32]
        def candidate():
            return c.inspect(limit=32)["operations"]
        a,b=baseline(),candidate()
        assert a==[{k:v for k,v in row.items() if k!="index"} for row in b]
        full=c.to_json(); page=c.inspect(limit=32)
        rows.append({"gate_count":n,"requested_operations":32,
            "baseline_full_replay_bytes":len(full.encode("utf-8")),
            "candidate_page_bytes":encoded(page),
            "same_selected_operations":True,**paired(baseline,candidate)})
    return rows

def evidence_context():
    rows=[]
    for n in (4,8,12):
        r=q.ghz(n).run()
        bits=["0"*n,"1"*n]
        full=r.math.probabilities()
        report=r.evidence(bits=bits)
        assert all(full[k]==report["basis"][k]["probability"] for k in bits)
        rows.append({"qubits":n,"selected_labels":2,
            "full_distribution_bytes":encoded(full),"targeted_evidence_bytes":encoded(report),
            "note":"different payloads: selected amplitudes+probabilities vs all probabilities"})
    return rows

if __name__=="__main__":
    print(json.dumps({"inspection":inspect_context(),"evidence":evidence_context(),
        "limits":"shared runner; selected operation extraction, not full replay equivalence; bytes not model tokens"},indent=2))
