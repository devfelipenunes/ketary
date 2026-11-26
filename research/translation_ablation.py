"""BENCH07: paired ablation of unconditional Qiskit lowering, research only."""
import argparse
import json
import math
import os
import platform
import statistics
from pathlib import Path
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit import Gate, Parameter
from qiskit.quantum_info import Statevector
from algorithm_matrix import catalog, corpus, lower, shape, state_for, verify_circuit, verify_vector, fetch_corpus
from combined_native_benchmark import rust_pack
from quest_probe import QuestProbe, pack, OPCODES
from longitudinal_benchmark import paired
from ketary._result import Result

def direct_or_rejection(c):
    # Only the strict native packer's explicit unsupported-input exception
    # is an exclusion. Unexpected failures propagate.
    try:
        return rust_pack(c),None
    except ValueError as exc:
        return None,str(exc)

def same_program(a,b):
    assert a[0]==b[0] and a[3]==b[3]
    np.testing.assert_array_equal(a[1],b[1])
    np.testing.assert_array_equal(a[2],b[2])

def regress(quest):
    for name in OPCODES:
        c=QuantumCircuit(3,global_phase=.37)
        args=(2,0) if name in ("cx","cz","swap") else (-.31,2) if name in ("rx","ry","rz","p") else (1,)
        getattr(c,name)(*args)
        p,error=direct_or_rejection(c)
        assert error is None
        same_program(p,pack(c))
        normalized=lower(c,1101)
        verify_circuit(c,normalized)
        for v in np.eye(8,dtype=np.complex128):
            expected=Statevector(v).evolve(c).data
            verify_vector(expected,quest.execute(p,v)[0])
            verify_vector(expected,quest.execute(rust_pack(normalized),v)[0])
    empty=QuantumCircuit(2,global_phase=.73)
    p,error=direct_or_rejection(empty)
    assert error is None
    v=state_for(2,1200)
    verify_vector(Statevector(v).evolve(empty).data,quest.execute(p,v)[0])
    bad=[]
    for label in ("cp","open_control","custom","symbolic","symbolic_phase","barrier","measurement","metadata","mcx"):
        c=QuantumCircuit(4,1) if label=="measurement" else QuantumCircuit(4)
        if label=="cp":c.cp(.3,0,1)
        elif label=="open_control":c.cx(0,1,ctrl_state=0)
        elif label=="custom":c.append(Gate("h",1,[]),[0])
        elif label=="symbolic":c.rx(Parameter("theta"),0)
        elif label=="symbolic_phase":c.global_phase=Parameter("phi")
        elif label=="barrier":c.barrier()
        elif label=="measurement":c.measure(0,0)
        elif label=="metadata":c.metadata={"tag":"do not discard"}
        else:c.mcx([0,2,3],1)
        p,error=direct_or_rejection(c)
        assert p is None and error,label
        bad.append({"case":label,"status":"DIRECT_REJECTED","reason":error})
    # Clean ancilla assumption must never leak into arbitrary input lowering.
    c=QuantumCircuit(5);c.mcx([0,2,4],1)
    verify_circuit(c,lower(c,1101))
    return bad

def benchmark_case(quest,c,name,family,seed,reps,source=None):
    direct,rejection=direct_or_rejection(c)
    normalized=lower(c,seed)
    verify_circuit(c,normalized)
    lowered=rust_pack(normalized)
    if direct is not None:
        same_program(direct,pack(c))
    results=[]
    for kind in ("zero","complex"):
        v=state_for(c.num_qubits,seed) if kind=="complex" else np.eye(1,1<<c.num_qubits,dtype=np.complex128).reshape(-1)
        # Same result validation and copy contract in every QuEST variant.
        def run(program):
            return Result(quest.execute(program,v)[0]).math.statevector()
        def native():
            return Statevector(v).evolve(c).data.copy()
        def lower_run():
            return run(rust_pack(lower(c,seed)))
        funcs={"native":native,"forced_lower_pack_run":lower_run,
               "lowered_pack_run":lambda:run(rust_pack(normalized)),
               "lowered_prepared_run":lambda:run(lowered)}
        if direct is not None:
            funcs.update(direct_pack_run=lambda:run(rust_pack(c)),direct_prepared_run=lambda:run(direct))
        expected=native()
        errors={k:verify_vector(expected,fn()) for k,fn in funcs.items()}
        timing=paired(funcs,reps,seed+(kind=="complex"))
        samples=timing["samples"]
        ratios=None
        if direct is not None:
            a=samples["direct_pack_run"]["raw_ms"];b=samples["forced_lower_pack_run"]["raw_ms"]
            ratios={"forced_over_direct_paired_median":statistics.median(y/x for x,y in zip(a,b,strict=True)),
                    "forced_minus_direct_paired_median_ms":statistics.median(y-x for x,y in zip(a,b,strict=True))}
        results.append({"input":kind,"validation":errors,"ablation":ratios,**timing})
    # Separate preparation-only experiments. Here 'native' means lowering,
    # not Statevector; do not compare these ratios with execution ratios.
    prep={"native":lambda:lower(c,seed),"lower_and_pack":lambda:rust_pack(lower(c,seed)),
          "pack_lowered":lambda:rust_pack(normalized)}
    if direct is not None:prep["pack_direct"]=lambda:rust_pack(c)
    ptime=paired(prep,reps,seed+9)
    pms=ptime["samples"]["lower_and_pack"]["median_ms"]
    direct_pms=ptime["samples"]["pack_direct"]["median_ms"] if direct is not None else None
    for row in results:
        med={k:s["median_ms"] for k,s in row["samples"].items()}
        for label,cost,run in (("lowered",pms,"lowered_prepared_run"),("direct",direct_pms,"direct_prepared_run")):
            if cost is None:continue
            saving=med["native"]-med[run]
            # Strict crossover for the additive median model, not measured batch speed.
            row[label+"_break_even_repeats"]=math.floor(cost/saving)+1 if saving>0 else None
    row={"name":name,"family":family,"original":shape(c),"lowered":shape(normalized),
         "source_blob":source,"direct_status":"SUPPORTED" if direct is not None else "REJECTED",
         "direct_rejection":rejection,"preparation":ptime,"execution":results}
    print(json.dumps({"name":name,"family":family,"n":c.num_qubits,"direct_status":row["direct_status"],
        "original_gates":len(c.data),"lowered_gates":len(normalized.data),
        "prep_medians_ms":{k:s["median_ms"] for k,s in ptime["samples"].items()},
        "execution":[{"input":x["input"],"medians_ms":{k:s["median_ms"] for k,s in x["samples"].items()},
                      "ablation":x["ablation"],"direct_break_even_repeats":x.get("direct_break_even_repeats"),
                      "lowered_break_even_repeats":x.get("lowered_break_even_repeats")} for x in results]}),flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--library",type=Path)
    p.add_argument("--suite",choices=["algorithms","gates","corpus"],default="algorithms")
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--repetitions",type=int,default=15)
    p.add_argument("--output",type=Path)
    p.add_argument("--corpus-root",type=Path)
    p.add_argument("--fetch-corpus",type=Path)
    p.add_argument("--smoke",action="store_true")
    a=p.parse_args()
    if a.fetch_corpus:
        fetch_corpus(a.fetch_corpus);return
    if not a.library or not a.output or not 3<=a.repetitions<=100 or os.getenv("OMP_NUM_THREADS")!="1":
        p.error("library, output, 3..100 reps and one thread required")
    if a.suite=="corpus" and not a.corpus_root:p.error("corpus root required")
    quest=QuestProbe(a.library,1)
    try:
        negative=regress(quest);rows=[];excluded=[]
        for name,family,n,native,_ in catalog(a.suite,a.seed,a.smoke):
            rows.append(benchmark_case(quest,native(),name,family,a.seed,a.repetitions))
        if a.suite=="corpus":
            cases,excluded=corpus(a.corpus_root)
            if len(cases)<10:raise AssertionError("unexpected corpus coverage")
            for name,c,removed,sha in cases:
                row=benchmark_case(quest,c,name,"published_unitary_projection",a.seed,a.repetitions,sha)
                row["projection_removed"]=removed
                rows.append(row)
        assert rows
        a.output.write_text(json.dumps({"scope":"paired shared-runner ablation, no hidden fallback",
            "suite":a.suite,"seed":a.seed,"repetitions":a.repetitions,"qiskit":qiskit.__version__,
            "numpy":np.__version__,"platform":platform.platform(),"affinity":sorted(os.sched_getaffinity(0)),
            "negative_controls":negative,"rows":rows,"excluded":excluded},indent=2,allow_nan=False))
    finally:quest.close()

if __name__=="__main__":main()
