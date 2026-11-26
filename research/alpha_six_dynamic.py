"""#157 bounded direct feed-forward and explicit native nested conditions."""
import inspect,json,random,time
import ketary as q
from qiskit import QuantumCircuit
from research.wave1_dynamic_protocols import native_counts
from research.circuit_rewrite_ladder import metrics,stats

def sdk_direct(random_input):
    c=q.Circuit.classical(3,3)
    if random_input:c.h(0)
    else:c.x(0)
    c.measure(0,0).reset(0).h(2)
    return c.if_x(1,0).if_z(2,0).h(2).measure([1,2],[1,2])

def native_direct(random_input):
    c=QuantumCircuit(3,3)
    if random_input:c.h(0)
    else:c.x(0)
    c.measure(0,0);c.reset(0);c.h(2)
    with c.if_test((c.clbits[0],1)):c.x(1)
    with c.if_test((c.clbits[0],1)):c.z(2)
    c.h(2);c.measure([1,2],[1,2])
    return c

def native_nested(random_input):
    c=QuantumCircuit(3,3)
    if random_input:c.h([0,1])
    else:c.x(0)
    c.measure([0,1],[0,1])
    with c.if_test((c.clbits[0],1)) as other:
        with c.if_test((c.clbits[1],0)):c.x(2)
    with other:
        with c.if_test((c.clbits[1],1)):c.x(2)
    c.measure(2,2)
    return c

def sdk_nested(random_input):
    return q.Circuit.from_dynamic(native_nested(random_input))

def expanded(c):
    return sum(1+sum(expanded(b) for b in getattr(item.operation,"blocks",())) for item in c.data)

def expected(kind,random_input):
    if kind=="direct":return {"000":.5,"111":.5} if random_input else {"111":1.}
    return {"000":.25,"101":.25,"110":.25,"011":.25} if random_input else {"101":1.}

def evaluate(kind,random_input,seed,reps=3,shots=2048):
    routes={"ketary":sdk_direct if kind=="direct" else sdk_nested,"qiskit":native_direct if kind=="direct" else native_nested}
    want=expected(kind,random_input);rng=random.Random(seed);out={}
    for key,fn in routes.items():
        c=fn(random_input);raw=c.to_qiskit() if key=="ketary" else c
        source=inspect.getsource(fn)
        if key=="ketary" and kind=="nested":source+="\n"+inspect.getsource(native_nested)
        if key=="qiskit":source+="\n"+inspect.getsource(native_counts)
        out[key]=dict(source=source,metrics=metrics(source),logical_instructions=len(raw.data),expanded_instructions=expanded(raw),build=[],run=[],counts=[])
    for i in range(reps):
        for key in rng.sample(list(routes),2):
            t=time.perf_counter_ns();c=routes[key](random_input);b=time.perf_counter_ns()
            s=seed+i
            if key=="ketary":
                report=c.run_shots(shots=shots,seed=s);counts=report.counts
                assert tuple(sorted(report.measured_bits))==(0,1,2)
            else:counts=native_counts(c,shots,s)
            e=time.perf_counter_ns()
            assert sum(counts.values())==shots and set(counts)<=set(want)
            if not random_input:assert counts=={next(iter(want)):shots}
            else:assert all(abs(counts.get(k,0)/shots-p)<.12 for k,p in want.items())
            out[key]["build"].append((b-t)/1e6);out[key]["run"].append((e-b)/1e6)
            out[key]["counts"].append(dict(seed=s,counts=counts))
    for row in out.values():
        for k in ("build","run"):row[k]=stats(row[k])
    return dict(kind=kind,random_input=random_input,seed=seed,shots=shots,expected=want,paths=out)

def run(reps=3):
    return [evaluate(kind,random_input,seed,reps) for seed in (1101,2202,3303) for kind in ("direct","nested") for random_input in (False,True)]

if __name__=="__main__":
    print(json.dumps({"scope":"same local Aer shots and seeds, analytic deterministic and sampled distributions; nested import cost included, logical counts not physical gates; no hardware","rows":run()},indent=2,allow_nan=False))
