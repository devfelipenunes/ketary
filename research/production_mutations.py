"""Run declared source mutants in isolated disposable copies.

A mutant is killed only when its selected test reaches a pytest assertion/failure
with exit code 1. Import failures, timeouts and bad baseline are invalid evidence.
No modification to the working source tree or arbitrary code execution from input.
"""
import argparse,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MUTANTS=(
("wrong_y_phase","_result.py","phase=1j**y","phase=(-1j)**y","tests/test_production_math_oracles.py::test_born_and_pauli_expectation_variance"),
("density_conjugation","_result.py","(a@a.conj().T)/self._r._norm_sq","(a@a.T)/self._r._norm_sq","tests/test_production_math_oracles.py::test_reduced_density_schmidt_entropy"),
("identity_phase_sign","_ergonomics.py","phases.append(-angle/2)","phases.append(angle/2)","tests/test_production_math_oracles.py::test_exact_commuting_evolution_strict_phase"),
("jacobian_scale","_ergonomics.py","diff=.5*(a-b)","diff=.25*(a-b)","tests/test_production_math_oracles.py::test_shared_jacobian_against_closed_form"),
("commutator_sign","_observable.py","phase=2j*phase.imag","phase=-2j*phase.imag","tests/test_dx_coverage_promotions.py::test_pauli_algebra"),
("anticommutator_scale","_observable.py","phase=2*phase.real","phase=phase.real","tests/test_dx_coverage_promotions.py::test_pauli_algebra"),
("controlled_phase_loss","_transpilation.py","raw.append(circuit.to_qiskit().to_gate().control(controls,ctrl_state=state,annotated=False),range(raw.num_qubits))","source=circuit.to_qiskit();source.global_phase=0;raw.append(source.to_gate().control(controls,ctrl_state=state,annotated=False),range(raw.num_qubits))","tests/test_dx_coverage_promotions.py::test_control_phase"),
("register_bit_order","_classical.py",'key=label.replace(" ","")','key=label.replace(" ","")[::-1]',"tests/test_dx_execution_coverage.py::test_dynamic_multiple_register_shots"),
)

def run_test(root,node):
    env=dict(os.environ,PYTHONPATH=str(root/"src"),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    check=subprocess.run([sys.executable,"-c","import pathlib,ketary; assert pathlib.Path(ketary.__file__).resolve().is_relative_to(pathlib.Path('src').resolve())"],cwd=root,env=env,capture_output=True,text=True,timeout=20)
    if check.returncode:raise RuntimeError("isolated import preflight failed: "+check.stderr[-1000:])
    start=time.monotonic()
    out=subprocess.run([sys.executable,"-m","pytest","-q","--import-mode=importlib",node],cwd=root,env=env,capture_output=True,text=True,timeout=120)
    log=out.stdout+out.stderr
    return {"exit":out.returncode,"seconds":time.monotonic()-start,"log":log[-6000:]}
def evaluate(mutant):
    name,file,old,new,node=mutant
    with tempfile.TemporaryDirectory(prefix="ketary-mutant-") as tmp:
        root=Path(tmp)
        shutil.copytree(ROOT/"src",root/"src")
        testpath=node.split("::")[0]
        (root/"tests").mkdir()
        shutil.copy2(ROOT/testpath,root/testpath)
        target=root/"src"/"ketary"/file
        original=target.read_text()
        if original.count(old)!=1:raise RuntimeError("ambiguous or missing mutation anchor "+name)
        baseline=run_test(root,node)
        if baseline["exit"]!=0 or "passed" not in baseline["log"] or "skipped" in baseline["log"]:
            return dict(id=name,status="invalid_baseline",baseline=baseline)
        target.write_text(original.replace(old,new,1))
        # Avoid timestamp/size pyc reuse after a source mutation.
        for cache in root.rglob("__pycache__"):shutil.rmtree(cache)
        result=run_test(root,node)
        status="killed" if result["exit"]==1 and "FAILED" in result["log"] and "ERROR collecting" not in result["log"] else "survived" if result["exit"]==0 else "invalid"
        return dict(id=name,status=status,source=file,node=node,baseline=baseline,mutant=result)

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    rows=[]
    for m in MUTANTS:
        row=evaluate(m);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="eight declared source mutants; not general mutation coverage",rows=rows),indent=2))
    if any(r["status"]!="killed" for r in rows):raise SystemExit(1)
if __name__=="__main__":main()
