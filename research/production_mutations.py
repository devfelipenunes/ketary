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
("controlled_shift_correction","_ergonomics.py","correction=(1-sqrt(2))/4","correction=0","tests/test_production_controlled_gradient.py::test_both_controlled_frequencies"),
("register_bit_order","_classical.py",'key=label.replace(" ","")','key=label.replace(" ","")[::-1]',"tests/test_dx_execution_coverage.py::test_dynamic_multiple_register_shots"),
("sequential_real_sum","_observable.py","real=fsum(z.real for z in values)","real=__import__('functools').reduce(lambda a,z:a+z.real,values,0.0)","tests/test_production_pauli_robustness.py::test_duplicate_real_cancellation"),
("sequential_imaginary_sum","_observable.py","imag=fsum(z.imag for z in values)","imag=__import__('functools').reduce(lambda a,z:a+z.imag,values,0.0)","tests/test_production_pauli_robustness.py::test_duplicate_imaginary_residual_rejected"),
("ignore_nonhermitian","_observable.py","if any(value.imag!=0 for value in terms.values()):","if False:","tests/test_production_pauli_robustness.py::test_duplicate_imaginary_residual_rejected"),
("pauli_xy_sign","_observable.py","(\"X\",\"Y\"):(\"Z\",1j)","(\"X\",\"Y\"):(\"Z\",-1j)","tests/test_production_pauli_robustness.py::test_pauli_algebra_dense_oracle"),
("pauli_yx_sign","_observable.py","(\"Y\",\"X\"):(\"Z\",-1j)","(\"Y\",\"X\"):(\"Z\",1j)","tests/test_production_pauli_robustness.py::test_pauli_algebra_dense_oracle"),
("discard_product_terms","_observable.py","out.setdefault(key,[]).append(complex(_real(value.real),_real(value.imag)))","out[key]=[complex(_real(value.real),_real(value.imag))]","tests/test_production_pauli_robustness.py::test_product_cancellation_identity"),
("complex_imaginary_sign","_result.py","imag=math.fsum(im*cache[label] for label,re,im in terms)","imag=-math.fsum(im*cache[label] for label,re,im in terms)","tests/test_production_channels_complex.py::test_complex_pauli_expectation"),
("channel_ignored","_classical.py","result=state.evolve(owned)","result=state","tests/test_production_channels_complex.py::test_amplitude_damping_oracle"),
("channel_preflight_ignored","_classical.py","if not owned.is_cptp(atol=1e-9,rtol=0):","if False:","tests/test_production_channels_complex.py::test_channel_rejects_before_execution"),
("controlled_shift_frequency","_ergonomics.py","shifts=(pi/2,-pi/2,pi,-pi) if four else (pi/2,-pi/2)","shifts=(pi/2,-pi/2,pi/2,-pi/2) if four else (pi/2,-pi/2)","tests/test_production_controlled_gradient.py::test_both_controlled_frequencies"),
("nested_depth_bypass","_classical.py","if depth>=3:","if depth>=4:","tests/test_production_nested_dynamic.py::test_nested_depth_and_expanded_budget"),
("expanded_count_bypass","_classical.py","if work>1024:","if work>2048:","tests/test_production_nested_dynamic.py::test_nested_depth_and_expanded_budget"),
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
    a.output.write_text(json.dumps(dict(scope=f"{len(MUTANTS)} declared source mutants; not general mutation coverage",rows=rows),indent=2))
    if any(r["status"]!="killed" for r in rows):raise SystemExit(1)
if __name__=="__main__":main()
