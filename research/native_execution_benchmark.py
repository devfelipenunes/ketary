"""Matched CPU execution and native boundary audit; no timing assertions."""
import argparse
import json
import os
import platform
import random
import sys
import time
from pathlib import Path
import numpy as np
import qiskit
import qiskit_aer
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
import ketary as q
from ketary._result import Result
from longitudinal_benchmark import paired, describe
from quest_probe import QuestProbe,pack,OPCODES

TOL=1e-9

def circuit(n,gates,seed):
    rng=random.Random(seed)
    c=QuantumCircuit(n,global_phase=.37)
    for _ in range(gates):
        name=rng.choice(list(OPCODES))
        if name in {"cx","cz","swap"}:
            getattr(c,name)(*rng.sample(range(n),2))
        elif name in {"rx","ry","rz","p"}:
            getattr(c,name)(rng.uniform(-3,3),rng.randrange(n))
        else:
            getattr(c,name)(rng.randrange(n))
    return c

def prepare_aer(c,state):
    work=QuantumCircuit(c.num_qubits)
    work.set_statevector(state)
    work.compose(c,inplace=True)
    # set_statevector may overwrite Aer circuit phase. Make this contract
    # explicit: evolve with phase zero and apply exactly once on export.
    phase=float(work.global_phase)
    work.global_phase=0.
    work.save_statevector()
    return work,phase

def aer_execute(sim,prepared):
    work,phase=prepared
    result=sim.run(work,shots=1).result()
    if not result.success:
        raise RuntimeError(str(result.status))
    output=np.array(result.data(0)["statevector"],dtype=np.complex128,copy=True)
    if phase:
        output *= np.exp(1j*phase)
    return output

def exact_checks(quest,sim):
    n=3
    for name in OPCODES:
        c=QuantumCircuit(n,global_phase=.41)
        if name in {"cx","cz","swap"}:
            getattr(c,name)(2,0)
        elif name in {"rx","ry","rz","p"}:
            getattr(c,name)(-.73,1)
        else:
            getattr(c,name)(1)
        prog=pack(c)
        for i in range(1<<n):
            state=np.eye(1<<n,dtype=np.complex128)[i]
            expected=Statevector(state).evolve(c).data
            np.testing.assert_allclose(quest.execute(prog,state)[0],expected,atol=TOL,rtol=0,err_msg=f'QuEST {name} basis {i}')
            np.testing.assert_allclose(aer_execute(sim,prepare_aer(c,state)),expected,atol=TOL,rtol=0,err_msg=f'Aer {name} basis {i}')
    c=QuantumCircuit(2)
    c.barrier()
    try:
        pack(c)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported instruction was silently accepted")
    return len(OPCODES)*8

def run(quest,threads,reps,seed,smoke):
    sim=AerSimulator(method="statevector",device="CPU",precision="double",
                     max_parallel_threads=threads,max_parallel_experiments=1,
                     max_parallel_shots=1,statevector_parallel_threshold=1)
    nofusion=AerSimulator(method="statevector",device="CPU",precision="double",
                          max_parallel_threads=threads,max_parallel_experiments=1,
                          max_parallel_shots=1,statevector_parallel_threshold=1,
                          fusion_enable=False)
    checks=exact_checks(quest,sim)
    rows=[]
    cases=[(4,20),(8,32)] if smoke else [(4,100),(8,1000),(12,256),(16,256),(18,128),(20,64),(22,32)]
    for n,gates in cases:
        c=circuit(n,gates,seed+n)
        sdk=q.from_qiskit(c)
        rng=np.random.default_rng(seed+n)
        state=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
        state/=np.linalg.norm(state)
        prog=pack(c)
        work=prepare_aer(c,state)
        phases=[]
        def quest_full():
            out,times=quest.execute(pack(c),state)
            phases.append(times.tolist())
            return Result(out).math.statevector()
        def quest_prepared():
            out,times=quest.execute(prog,state)
            return Result(out).math.statevector()
        def aer_full():
            return Result(aer_execute(sim,prepare_aer(c,state))).math.statevector()
        funcs={
            "native":lambda:Statevector(state).evolve(c).data.copy(),
            "ketary":lambda:sdk.run(initial_state=state).math.statevector(),
            "aer_end_to_end":aer_full,
            "aer_prepared":lambda:Result(aer_execute(sim,work)).math.statevector(),
            "aer_no_fusion":lambda:Result(aer_execute(nofusion,work)).math.statevector(),
            "quest_end_to_end":quest_full,
            "quest_prepared":quest_prepared,
        }
        expected=funcs["native"]()
        errors={}
        for name,fn in funcs.items():
            observed=fn()
            np.testing.assert_allclose(observed,expected,atol=TOL,rtol=0)
            if abs(np.vdot(observed,observed).real-1)>TOL:
                raise AssertionError("normalization")
            errors[name]=float(np.max(abs(expected-observed)))
        phases.clear()
        result=paired(funcs,reps,seed+n)
        phase_summary={name:describe([row[i] for row in phases[3:]]) for i,name in enumerate(
            ("allocate_input","native_gates","export_destroy"))}
        pack_times=[]
        copy_times=[]
        validate_times=[]
        for _ in range(reps):
            t=time.perf_counter_ns(); pack(c); pack_times.append((time.perf_counter_ns()-t)/1e6)
            t=time.perf_counter_ns(); state.copy(); copy_times.append((time.perf_counter_ns()-t)/1e6)
            t=time.perf_counter_ns(); Result(state); validate_times.append((time.perf_counter_ns()-t)/1e6)
        row={"n":n,"gates":gates,"state_bytes":state.nbytes,"max_error":errors,
             "quest_phases":phase_summary,"pack":describe(pack_times),
             "array_copy":describe(copy_times),"result_validate_copy":describe(validate_times),**result}
        rows.append(row)
        print(json.dumps({"n":n,"gates":gates,"medians_ms":{k:v["median_ms"] for k,v in result["samples"].items()},
                          "quest_phase_ms":{k:v["median_ms"] for k,v in phase_summary.items()},
                          "max_error":errors}),file=sys.stderr,flush=True)
    return {"scope":"CPU only, double precision, shared CI; explicit engines, no auto-routing",
            "seed":seed,"threads":threads,"repetitions":reps,"basis_checks_per_engine":checks,
            "qiskit":qiskit.__version__,"aer":qiskit_aer.__version__,"numpy":np.__version__,
            "platform":platform.platform(),"affinity":sorted(os.sched_getaffinity(0)),
            "cases":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library",type=Path,required=True)
    p.add_argument("--threads",type=int,choices=[1,2,4,8],default=1)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--smoke",action="store_true")
    a=p.parse_args()
    if not 3<=a.repetitions<=100 or (not a.smoke and a.repetitions<20):
        p.error("20..100 repetitions (smoke >=3)")
    if os.environ.get("OMP_NUM_THREADS")!=str(a.threads):
        p.error("set OMP_NUM_THREADS before starting Python")
    quest=QuestProbe(a.library,a.threads)
    try:
        print(json.dumps(run(quest,a.threads,a.repetitions,a.seed,a.smoke),indent=2,allow_nan=False))
    finally:
        quest.close()
