"""Explicit dedicated-host benchmark harness. Never provisions a host.

Run only on an authorized isolated Linux host with the pinned environment.
Results do not establish isolation independently of the operator's attestation.
"""
import argparse,hashlib,importlib.metadata,json,os,platform,shutil,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
THREADS={"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1"}
def command_plan():
    """Fixed benchmark protocol; three independent complete sets."""
    commands=[
        ("baseline",[sys.executable,"benchmark.py","--repetitions","30"],"benchmark.json"),
        ("fluent",[sys.executable,"-m","research.fluent_scalar_dispatch","--output","fluent.json","--repetitions","30"],None),
        ("pauli",[sys.executable,"-m","research.scalar_pauli_clamp","--output","pauli.json","--repetitions","30"],None),
        ("batches",[sys.executable,"-m","research.batch_ingestion","--output","batches.json","--repetitions","30"],None),
        ("trace-index",[sys.executable,"-m","research.trace_wire_index_rss","--output","trace-rss.json","--repetitions","30"],None),
        ("singleton-tails",[sys.executable,"-m","research.performance_tail_and_singleton","--output","tails.json","--repetitions","30"],None),
        ("native-finite",[sys.executable,"-m","research.native_finite_scan","--output","finite.json","--repetitions","30"],None),
        ("simd",[sys.executable,"-m","research.explicit_simd_finite_scan","--output","simd.json","--repetitions","30"],None),
        ("cold-pool",[sys.executable,"-m","research.explicit_sweep_parallelism","--output","parallel.json","--repetitions","5"],None),
        ("warm-pool",[sys.executable,"-m","research.warm_sweep_pool","--output","warm.json","--repetitions","10"],None),
        ("suffix",[sys.executable,"-m","research.composition_suffix_transaction","--output","suffix.json","--repetitions","30"],None),
        ("trace-terminal",[sys.executable,"-m","research.trace_terminal_snapshot","--output","terminal.json","--repetitions","30"],None),
        ("memory",[sys.executable,"-m","research.performance_memory_closure","--output","memory.json"],None)]
    return commands

def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def preflight(output):
    if not sys.platform.startswith("linux") or sys.version_info[:2]!=(3,12):
        raise RuntimeError("dedicated protocol requires Linux and Python 3.12")
    if output==ROOT or ROOT in output.parents:
        raise ValueError("output must be outside checkout")
    if output.exists():
        raise FileExistsError("output must be a new directory")
    if git("status","--porcelain"):
        raise RuntimeError("clean checkout required")
    for binary in ("git","c++","rustc"):
        if not shutil.which(binary):raise RuntimeError(f"missing research toolchain: {binary}")
    pinned=next(x.split("==",1)[1].strip() for x in (ROOT/"requirements.txt").read_text().splitlines() if x.startswith("qiskit==")) if any(x.startswith("qiskit==") for x in (ROOT/"requirements.txt").read_text().splitlines()) else "2.6.2"
    actual=importlib.metadata.version("qiskit")
    if actual!=pinned:raise RuntimeError(f"Qiskit version mismatch: {actual} != {pinned}")
    return dict(commit=git("rev-parse","HEAD"),python=sys.version,platform=platform.platform(),
                affinity=sorted(os.sched_getaffinity(0)),qiskit=actual,
                thread_limits=THREADS,operator_attestation="authorized isolated host; not independently verified",
                cpuinfo=Path("/proc/cpuinfo").read_text(),meminfo=Path("/proc/meminfo").read_text(),
                cpp=subprocess.check_output(["c++","--version"],text=True),
                rust=subprocess.check_output(["rustc","--version"],text=True))

def write_json(path,data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")

def run_step(name,argv,stdout_name,folder,env):
    stdout=folder/(stdout_name or f"{name}.stdout.log")
    stderr=folder/f"{name}.stderr.log"
    start=time.monotonic()
    with stdout.open("w") as out,stderr.open("w") as err:
        result=subprocess.run(argv,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=3600,check=False)
    return dict(name=name,argv=argv,returncode=result.returncode,seconds=time.monotonic()-start,
                stdout=stdout.name,stderr=stderr.name)

def execute(output,meta):
    output.mkdir(parents=True)
    env=dict(os.environ,**THREADS)
    write_json(output/"host.json",meta)
    (output/"environment.txt").write_text(subprocess.check_output([sys.executable,"-m","pip","freeze"],cwd=ROOT,env=env,text=True))
    manifest={"status":"IN_PROGRESS","commit":meta["commit"],"steps":[]}
    def record(entry):
        manifest["steps"].append(entry);write_json(output/"manifest.json",manifest)
        if entry["returncode"]!=0:raise RuntimeError(f"failed step: {entry['name']}")
    try:
        record(run_step("tests",[sys.executable,"-m","pytest","-q","-rs","tests","research/probes"],None,output,env))
        for rep in range(1,4):
            folder=output/f"run-{rep}";folder.mkdir()
            for name,args,stdout in command_plan():
                args=list(args)
                # Explicit output arguments are rewritten to absolute paths;
                # commands always run from the same clean checkout.
                if "--output" in args:
                    i=args.index("--output")+1
                    args[i]=str(folder/args[i])
                entry=run_step(name,args,stdout,folder,env);entry["run"]=rep
                record(entry)
        if git("rev-parse","HEAD")!=meta["commit"] or git("status","--porcelain"):
            raise RuntimeError("checkout changed during qualification")
        manifest["status"]="MEASURED_REVIEW_REQUIRED"
    except Exception as exc:
        manifest["status"]="FAILED_OR_INCOMPLETE";manifest["error"]=str(exc)
        raise
    finally:
        manifest["sha256"]={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.rglob("*")) if p.is_file() and p.name!="manifest.json"}
        write_json(output/"manifest.json",manifest)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path)
    p.add_argument("--acknowledge-isolated-host",action="store_true")
    p.add_argument("--plan",action="store_true")
    a=p.parse_args()
    if a.plan:
        print(json.dumps({"repetitions":3,"commands":command_plan()},indent=2));return
    if not a.output or not a.acknowledge_isolated_host:
        p.error("execution requires --output and --acknowledge-isolated-host")
    out=a.output.resolve()
    execute(out,preflight(out))
if __name__=="__main__":main()
