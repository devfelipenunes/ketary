"""Static cost-site inventory and public native instruction-access experiments.

Research only. Static sites are leads, not runtime call counts or quality scores.
"""
import argparse
import ast
import json
import random
import time
import platform
from pathlib import Path
from collections import Counter
from importlib.metadata import version
from qiskit import QuantumCircuit
from research.architecture_inventory import inspect
from research.circuit_rewrite_ladder import stats

CATEGORIES={
    "copy": {"copy","deepcopy","to_qiskit","statevector","to_matrix"},
    "native_materialization": {"operation","Operator","Statevector","find_bit","assign_parameters","transpile"},
    "allocation": {"array","asarray","zeros","zeros_like","empty","empty_like","arange","concatenate","stack","kron"},
    "linear_algebra": {"norm","vdot","dot","evolve","svd","eigvalsh","eigh","expm"},
    "serialization": {"dumps","loads","to_json","from_json"},
    "validation": {"_angle","_real","_int","_limit","_require_bound","_validate","_validate_bound_values"},
}

def inventory(root=None):
    root=Path(__file__).resolve().parents[1] if root is None else Path(root)
    graph=inspect(root)
    result=[]
    for path in sorted((root/"src/ketary").glob("*.py")):
        tree=ast.parse(path.read_text())
        sites={k:[] for k in CATEGORIES}
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else None
            elif isinstance(node,ast.Attribute) and node.attr=="operation":
                name=node.attr
            else:continue
            for category,names in CATEGORIES.items():
                if name in names:sites[category].append({"line":node.lineno,"symbol":name})
        result.append(dict(module=path.stem,**graph["module_stats"][path.stem],
                           outgoing=sorted(b for a,b in graph["internal_imports"] if a==path.stem),
                           cost_sites={k:sorted(v,key=lambda x:(x["line"],x["symbol"])) for k,v in sites.items()}))
    return {"scope":"AST syntax leads, not call frequencies, allocation counts or measured costs",
            "modules":result,"eager_cycles":graph["eager_cycles"],"cycles":graph["cycles"],
            "duplicate_bodies":graph["exact_duplicate_body_groups"]}

def build(n,gates,rng):
    c=QuantumCircuit(n,global_phase=.17)
    for i in range(gates):
        wire=i%n
        if i%3==0:c.ry(rng.uniform(-1,1),wire)
        elif i%3==1:c.cx(wire,(wire+1)%n)
        else:c.h(wire)
    return c

def rows_baseline(c):
    return tuple((item.operation.name,tuple(item.operation.params),tuple(c.find_bit(w).index for w in item.qubits))
                 for item in c.data)

def rows_native(c):
    indices={w:i for i,w in enumerate(c.qubits)}
    return tuple((item.name,tuple(item.params),tuple(indices[w] for w in item.qubits)) for item in c.data)

def run(seed,reps,quick=False):
    rng=random.Random(seed)
    rows=[]
    configs=((4,10),(8,100)) if quick else tuple((n,g) for n in (4,8,12,20) for g in (10,50,100,500,1000))
    for n,gates in configs:
        c=build(n,gates,rng)
        before=c.copy()
        expected=rows_baseline(c)
        counts=dict(Counter(r[0] for r in expected))
        routes={"python_operation":lambda:rows_baseline(c),"instruction_fields":lambda:rows_native(c)}
        counts_routes={"python_count":lambda:dict(Counter(item.operation.name for item in c.data)),
                       "native_count":lambda:dict(c.count_ops())}
        timings={k:[] for k in (*routes,*counts_routes)}
        all_routes={**routes,**counts_routes}
        for _ in range(reps):
            for name in rng.sample(list(all_routes),len(all_routes)):
                t=time.perf_counter_ns();value=all_routes[name]();dt=(time.perf_counter_ns()-t)/1e6
                assert value==(expected if name in routes else counts)
                timings[name].append(dt)
        assert c==before
        rows.append(dict(n=n,gates=gates,seed=seed,paths={k:stats(v) for k,v in timings.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);p.add_argument("--quick",action="store_true");a=p.parse_args()
    if a.reps<1:p.error("positive reps required")
    print(json.dumps(dict(scope="public Qiskit inspection, identical output, no simulation, no installed changes",
        python=platform.python_version(),qiskit=version("qiskit"),numpy=version("numpy"),
        audit=inventory(),rows=[r for seed in (1101,2202,3303) for r in run(seed,a.reps,a.quick)]),indent=2,allow_nan=False))
