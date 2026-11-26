"""Matched algorithm, logical gate and published-corpus benchmark.

No external executable code, no timing-based pass/fail, no silent engine
fallback. Original and explicitly lowered basis are separately reported.
"""
import argparse
import json
import math
import os
import platform
import random
import re
import resource
import statistics
import subprocess
import sys
from pathlib import Path
from functools import partial
import numpy as np
import qiskit
import qiskit_aer
from qiskit import QuantumCircuit,transpile,qasm2
from qiskit.circuit.library import n_local
from qiskit.quantum_info import Statevector,Operator
from qiskit_aer import AerSimulator
import ketary as q
from ketary._gate_specs import SPECS
from ketary._result import Result
from longitudinal_benchmark import paired
from published_circuit_execution import MANIFEST,source_bytes,project_unitary
from native_execution_benchmark import prepare_aer,aer_execute
from quest_probe import QuestProbe,OPCODES

BASIS=list(OPCODES)
TOL=1e-9

def native_of(value):
    return value if isinstance(value,QuantumCircuit) else value.to_qiskit()

def qft_native(n,inverse=False):
    c=QuantumCircuit(n)
    for target in reversed(range(n)):
        c.h(target)
        for control in reversed(range(target)):
            c.cp(math.pi/2**(target-control),control,target)
    for i in range(n//2):c.swap(i,n-1-i)
    return c.inverse() if inverse else c

def ghz_native(n):
    c=QuantumCircuit(n);c.h(0)
    for i in range(1,n):c.cx(i-1,i)
    return c

def bv_native(mask):
    n=len(mask);c=QuantumCircuit(n+1);c.x(n);c.h(range(n+1))
    for i,bit in enumerate(reversed(mask)):
        if bit=="1":c.cx(i,n)
    c.h(range(n))
    return c

def simon_native(secret):
    n=len(secret);active=[i for i,b in enumerate(reversed(secret)) if b=="1"]
    pivot=active[0];c=QuantumCircuit(2*n);c.h(range(n))
    for i in range(n):
        if i!=pivot:
            c.cx(i,n+i)
            if i in active:c.cx(pivot,n+i)
    c.h(range(n))
    return c

def grover_native(mark,iterations):
    n=len(mark);c=QuantumCircuit(n);c.h(range(n))
    def flip(label):
        zero=[i for i,b in enumerate(reversed(label)) if b=="0"]
        for i in zero:c.x(i)
        if n==2:c.cz(0,1)
        else:c.h(2);c.ccx(0,1,2);c.h(2)
        for i in zero:c.x(i)
    for _ in range(iterations):
        flip(mark);c.h(range(n));flip("0"*n);c.h(range(n))
        c.global_phase+=math.pi
    return c

def qpe_native(phase,n):
    c=QuantumCircuit(n+1);c.x(n);c.h(range(n))
    for wire in range(n):c.cp(2*math.pi*((phase*(1<<wire))%1),wire,n)
    c.compose(qft_native(n,True),qubits=range(n),inplace=True)
    return c

def layered(n,depth,kind,sdk):
    c=q.Circuit(n) if sdk else QuantumCircuit(n)
    pairs=[(i,(i+1)%n) for i in range(n)]
    c.h(range(n))
    for d in range(depth):
        if kind=="graph":
            if sdk:c.cz(pairs=pairs)
            else:c.cz([a for a,b in pairs],[b for a,b in pairs])
            c.ry(.13*(d+1),range(n))
        elif kind=="qaoa":
            if sdk:c.rzz(.21*(d+1),pairs=pairs)
            else:c.rzz(.21*(d+1),[a for a,b in pairs],[b for a,b in pairs])
            c.rx(.17*(d+1),range(n))
        else:
            # First-order Ising/Trotter pattern; not a claim of physical accuracy.
            if sdk:c.rzz(.09,pairs=pairs)
            else:c.rzz(.09,[a for a,b in pairs],[b for a,b in pairs])
            c.rx(.07,range(n))
    return c

def variational(n,depth,sdk):
    if sdk:
        c=q.ansatz(n,rotations=("ry","rz"),reps=depth,entanglement="circular",prefix="w")
        return c.bind(np.linspace(-.3,.8,len(c.parameters)))
    c=n_local(n,rotation_blocks=["ry","rz"],entanglement_blocks="cx",
              entanglement="circular",reps=depth,parameter_prefix="w")
    return c.assign_parameters(np.linspace(-.3,.8,len(c.parameters)))

def gate_case(name,n,seed,sdk):
    c=q.Circuit(n) if sdk else QuantumCircuit(n)
    rng=random.Random(seed)
    for i in range(16):
        if name=="mcx":
            wires=rng.sample(range(n),4)
            c.mcx(wires[:3],wires[3])
        else:
            _,width,p,_,_=SPECS[name]
            wires=rng.sample(range(n),width)
            angles=[rng.uniform(-1,1) for _ in range(p)]
            getattr(c,name)(*angles,*wires)
    return c

def catalog(suite,seed,smoke):
    out=[]
    def add(name,family,n,native,sdk):
        out.append((name,family,n,native,sdk))
    if suite in ("algorithms","all"):
        for n in ([4] if smoke else [4,8,12,16]):
            add(f"ghz_{n}","ghz",n,partial(ghz_native,n),partial(q.ghz,n))
            add(f"qft_{n}","qft",n,partial(qft_native,n),partial(q.qft,n))
            for kind in ("graph","qaoa","trotter"):
                depth=3
                add(f"{kind}_{n}_d{depth}",kind,n,partial(layered,n,depth,kind,False),
                    partial(layered,n,depth,kind,True))
            add(f"variational_{n}_d3","variational",n,partial(variational,n,3,False),
                partial(variational,n,3,True))
        for n in ([3] if smoke else [3,7,11,15]):
            mask=("1011"*n)[:n]
            add(f"bv_{n}","bernstein_vazirani",n+1,partial(bv_native,mask),partial(q.bernstein_vazirani,mask))
        for n in ([3] if smoke else [3,5,7]):
            mask=("1011"*n)[:n]
            add(f"simon_{n}","simon",2*n,partial(simon_native,mask),partial(q.simon,mask))
        for label in (["101"] if smoke else ["10","101"]):
            add(f"grover_{label}","grover",len(label),partial(grover_native,label,2),
                partial(q.grover,label,iterations=2))
        for n in ([3] if smoke else [3,5,8]):
            add(f"qpe_{n}","phase_estimation",n+1,partial(qpe_native,.375,n),
                partial(q.phase_estimation,.375,precision=n))
    if suite in ("gates","all"):
        names=["h","cp","mcx"] if smoke else [*SPECS,"mcx"]
        for n in ([8] if smoke else [8,12]):
            for name in names:
                add(f"gate_{name}_{n}",f"gate:{name}",n,partial(gate_case,name,n,seed,False),
                    partial(gate_case,name,n,seed,True))
    return out

def corpus(root):
    manifest=json.loads(MANIFEST.read_text())
    out=[];excluded=[]
    for entry in manifest["files"]:
        name=entry["name"]
        source=source_bytes(entry,manifest["commit"],root).decode("utf-8")
        clean=re.sub(r"//[^\n]*","",source)
        if any(v!="qelib1.inc" for v in re.findall(r'\binclude\s+"([^"]+)"',clean)):
            raise ValueError("unexpected include")
        try:
            original=qasm2.loads(source,include_path=(),custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
        except qasm2.QASM2Error as exc:
            excluded.append({"name":name,"status":"PARSER_UNSUPPORTED","reason":str(exc)[:300]});continue
        logical,removed=project_unitary(original)
        if logical is None:
            excluded.append({"name":name,"status":"OUTSIDE_UNITARY_SCOPE","reason":removed});continue
        out.append((name,logical,removed,entry["git_blob_sha1"]))
    return out,excluded

def state_for(n,seed):
    rng=np.random.default_rng(seed+n)
    data=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    return data/np.linalg.norm(data)

def stats(data):
    for sample in data["samples"].values():
        raw=sample["raw_ms"]
        sample["mean_ms"]=statistics.mean(raw)
        sample["stdev_ms"]=statistics.stdev(raw)
        sample["mad_ms"]=statistics.median(abs(x-sample["median_ms"]) for x in raw)
        sample["p99_ms"]=float(np.percentile(raw,99))
    return data

def record(rows,name,stage,meta,funcs,reps,seed,verify):
    reference=funcs["native"]()
    errors={}
    for variant,fn in funcs.items():
        errors[variant]=verify(reference,fn())
    row={"name":name,"stage":stage,**meta,"validation":errors,
         **stats(paired(funcs,reps,seed+len(rows)))}
    rows.append(row)
    print(json.dumps({"name":name,"stage":stage,"n":meta["n"],
        "original_gates":meta["original_gates"],"lowered_gates":meta.get("lowered_gates"),
        "medians_ms":{k:v["median_ms"] for k,v in row["samples"].items()},
        "p95_ms":{k:v["p95_ms"] for k,v in row["samples"].items()},
        "validation":errors}),flush=True)
    return row

def verify_circuit(a,b):
    a,b=native_of(a),native_of(b)
    if a==b:return "exact native circuit equality"
    if a.num_qubits<=8:
        np.testing.assert_allclose(Operator(a).data,Operator(b).data,atol=TOL,rtol=0)
        return "strict full operator equality"
    for i in range(2):
        state=state_for(a.num_qubits,4000+i)
        np.testing.assert_allclose(Statevector(state).evolve(a).data,Statevector(state).evolve(b).data,atol=TOL,rtol=0)
    return "two selected complex states, not full operator proof"

def verify_vector(a,b):
    a,b=np.asarray(a),np.asarray(b)
    np.testing.assert_allclose(a,b,atol=TOL,rtol=0)
    if abs(np.vdot(b,b).real-1)>TOL:raise AssertionError("state normalization")
    return {"max_abs_error":float(np.max(np.abs(a-b))),"l2_error":float(np.linalg.norm(a-b)),
            "infidelity":float(max(0.,1-abs(np.vdot(a,b))**2))}

def shape(c):
    return {"n":c.num_qubits,"original_gates":len(c.data),"original_depth":c.depth(),
            "original_two_plus":sum(len(x.qubits)>=2 for x in c.data),
            "gate_histogram":{str(k):int(v) for k,v in c.count_ops().items()},
            "state_bytes":16*(1<<c.num_qubits)}

def lower(c,seed):
    return transpile(c,basis_gates=BASIS,optimization_level=0,seed_transpiler=seed)

def execute_case(rows,name,family,original,sdk,seed,reps,quest,sim,sim_nofusion,baseline,meta_extra=None):
    meta={"family":family,**shape(original),**(meta_extra or {})}
    n=original.num_qubits
    # Qiskit original vs actual SDK logical representation, no basis translation hidden in timing.
    for input_kind in ("zero","complex"):
        state=state_for(n,seed) if input_kind=="complex" else np.eye(1,1<<n,dtype=np.complex128).reshape(-1)
        def native():
            return Statevector.from_instruction(original).data.copy() if input_kind=="zero" else Statevector(state).evolve(original).data.copy()
        def sdk_exec():
            return sdk.run(initial_state=None if input_kind=="zero" else state).math.statevector()
        record(rows,name,"execute_original",{**meta,"input":input_kind},
               {"native":native,"ketary":sdk_exec},reps,seed,verify_vector)
    if baseline:return
    normalized=lower(original,seed)
    sdk_lower=q.from_qiskit(normalized)
    relation=verify_circuit(original,normalized)
    meta={**meta,"lowered_gates":len(normalized.data),"lowered_depth":normalized.depth(),
          "lowered_gate_histogram":{str(k):int(v) for k,v in normalized.count_ops().items()},
          "lowered_two_plus":sum(len(x.qubits)>=2 for x in normalized.data),"lowering_oracle":relation}
    state=state_for(n,seed)
    work=prepare_aer(normalized,state)
    from combined_native_benchmark import rust_pack
    prepared=rust_pack(normalized)
    def q_exec(program):
        return Result(quest.execute(program,state)[0]).math.statevector()
    funcs={"native":lambda:Statevector(state).evolve(normalized).data.copy(),
           "ketary":lambda:sdk_lower.run(initial_state=state).math.statevector(),
           "aer_prepared":lambda:Result(aer_execute(sim,work)).math.statevector(),
           "aer_no_fusion":lambda:Result(aer_execute(sim_nofusion,work)).math.statevector(),
           "quest_prepared":lambda:q_exec(prepared),
           "quest_rust_pack":lambda:q_exec(rust_pack(normalized)),
           "quest_full_lower":lambda:q_exec(rust_pack(lower(original,seed)))}
    ref=Statevector(state).evolve(original).data
    for name_,fn in funcs.items():verify_vector(ref,fn())
    record(rows,name,"execute_common_basis",{**meta,"input":"complex"},funcs,reps,seed,verify_vector)
    # Report compiler cost separately; do not call it simulator speed.
    record(rows,name,"lowering",meta,{"native":lambda:lower(original,seed)},reps,seed,verify_circuit)
    record(rows,name,"import",meta,{"native":lambda:normalized.copy(),
           "ketary":lambda:q.from_qiskit(normalized)},reps,seed,verify_circuit)

def shot_cases(rows,reps,seed):
    for family in ("ghz_shots","teleportation"):
        if family=="ghz_shots":
            n=8;c=QuantumCircuit(n,n);c.h(0)
            for i in range(1,n):c.cx(i-1,i)
            c.measure(range(n),range(n))
            sdk=q.Circuit.classical(n,n).h(0)
            for i in range(1,n):sdk.cx(i-1,i)
            sdk.measure(range(n),range(n))
        else:
            n=3;c=QuantumCircuit(3,3);c.ry(.41,0);c.rz(.72,0);c.h(1);c.cx(1,2)
            c.cx(0,1);c.h(0);c.measure(0,0);c.measure(1,1)
            with c.if_test((c.clbits[1],1)):c.x(2)
            with c.if_test((c.clbits[0],1)):c.z(2)
            c.rz(-.72,2);c.ry(-.41,2);c.measure(2,2)
            sdk=q.teleportation(.41,.72,verify=True)
        for shots in (128,1024,8192):
            def native():
                backend=AerSimulator(method="statevector",max_parallel_threads=1)
                compiled=transpile(c,backend=backend,optimization_level=0,seed_transpiler=seed)
                result=backend.run(compiled,shots=shots,seed_simulator=seed).result()
                if not result.success:raise RuntimeError("Aer shots failed")
                return result.get_counts()
            def actual():return sdk.run_shots(shots=shots,seed=seed).counts
            def verify(a,b):
                if sum(a.values())!=shots or sum(b.values())!=shots:raise AssertionError("shot count")
                allowed={"0"*n,"1"*n} if family=="ghz_shots" else {"000","001","010","011"}
                if not set(a)<=allowed or not set(b)<=allowed:raise AssertionError("unexpected support")
                tvd=sum(abs(a.get(k,0)-b.get(k,0)) for k in set(a)|set(b))/(2*shots)
                # Identical backend, fixed seed and same logical operations.
                # Require exact counts for this reproducibility study.
                if a!=b:raise AssertionError(f"seeded counts differ: TVD {tvd}")
                return {"total_variation_distance":tvd,"shots":shots}
            record(rows,family,"shots",{**shape(c),"shots":shots,"family":family},
                   {"native":native,"ketary":actual},reps,seed,verify)

def run(a,quest):
    rows=[];excluded=[]
    sim=AerSimulator(method="statevector",device="CPU",precision="double",max_parallel_threads=1)
    nofusion=AerSimulator(method="statevector",device="CPU",precision="double",max_parallel_threads=1,fusion_enable=False)
    for name,family,n,native,sdk in catalog(a.suite,a.seed,a.smoke):
        c=native();s=sdk()
        verify_circuit(c,s)
        record(rows,name,"build",{"family":family,**shape(c)},
               {"native":native,"ketary":sdk},a.repetitions,a.seed,verify_circuit)
        execute_case(rows,name,family,c,s,a.seed,a.repetitions,quest,sim,nofusion,a.baseline_only)
    if a.suite in ("corpus","all") and a.corpus_root:
        cs,excluded=corpus(a.corpus_root)
        if len(cs)<10:raise AssertionError("corpus projection count below expected minimum")
        for name,c,removed,sha in cs:
            try:
                s=q.from_qiskit(c);path="direct"
            except (TypeError,ValueError):
                # Explicit import normalization, separate from common 11-gate basis.
                s=q.from_qiskit(transpile(c,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=a.seed))
                path="u/cx import translation"
            verify_circuit(c,s)
            execute_case(rows,name,"published_qasm",c,s,a.seed,a.repetitions,quest,sim,nofusion,a.baseline_only,
                         {"source_blob":sha,"removed":removed,"sdk_import_path":path})
    if a.suite in ("algorithms","all") and not a.smoke:
        shot_cases(rows,a.repetitions,a.seed)
    return {"scope":"matched shared runner; research engines explicit; strict complex states",
            "revision_label":a.label,"seed":a.seed,"repetitions":a.repetitions,
            "suite":a.suite,"python":sys.version,"qiskit":qiskit.__version__,
            "aer":qiskit_aer.__version__,"numpy":np.__version__,"platform":platform.platform(),
            "affinity":sorted(os.sched_getaffinity(0)),"process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "rows":rows,"excluded":excluded}

def fetch_corpus(root):
    manifest=json.loads(MANIFEST.read_text())
    for entry in manifest["files"]:
        dest=root/entry["path"];dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(source_bytes(entry,manifest["commit"],None))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--suite",choices=["all","algorithms","gates","corpus"],default="all")
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--label",default="current")
    p.add_argument("--output",type=Path)
    p.add_argument("--library",type=Path)
    p.add_argument("--corpus-root",type=Path)
    p.add_argument("--fetch-corpus",type=Path)
    p.add_argument("--baseline-only",action="store_true")
    p.add_argument("--smoke",action="store_true")
    a=p.parse_args()
    if a.fetch_corpus:
        fetch_corpus(a.fetch_corpus);return
    if not a.output or not 3<=a.repetitions<=100 or not (a.baseline_only or a.library):
        p.error("output, 3..100 repetitions and library unless baseline-only required")
    if a.suite in ("corpus","all") and not a.corpus_root and not a.smoke:
        p.error("corpus root required")
    quest=None if a.baseline_only else QuestProbe(a.library,1)
    try:a.output.write_text(json.dumps(run(a,quest),indent=2,allow_nan=False))
    finally:
        if quest:quest.close()

if __name__=="__main__":main()
