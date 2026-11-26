"""Run declared source mutants in isolated disposable copies.

A mutant is killed only when its selected test reaches a pytest assertion/failure
with exit code 1. Import failures, timeouts and bad baseline are invalid evidence.
No modification to the working source tree or arbitrary code execution from input.
"""
import argparse,json,os,shutil,subprocess,sys,tempfile,time,re
import xml.etree.ElementTree as ET
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
("qgt_rotation_scale","_ergonomics.py","factor=.5 if name in phases else 1/(2*sqrt(2))","factor=.5 if name in phases else .5","tests/test_production_qgt.py::test_qgt_bloch"),
("qgt_phase_scale","_ergonomics.py","factor=.5 if name in phases else 1/(2*sqrt(2))","factor=1/(2*sqrt(2))","tests/test_production_qgt.py::test_qgt_controlled_shared_and_phase"),
("qgt_projection_omitted","_ergonomics.py","projected=derivatives-psi[:,None]*(psi.conj()@derivatives)[None,:]/np.vdot(psi,psi).real","projected=derivatives","tests/test_production_qgt.py::test_qgt_bloch"),
("qgt_wrong_conjugation","_ergonomics.py","Q=projected.conj().T@projected","Q=projected.T@projected","tests/test_production_qgt.py::test_qgt_bloch"),
("qgt_chain_weight_ignored","_ergonomics.py","derivatives[:,j]+=w*delta","derivatives[:,j]+=delta","tests/test_production_qgt.py::test_qgt_controlled_shared_and_phase"),
("qgt_occurrence_cap","_ergonomics.py","if len(staged)>32:","if len(staged)>64:","tests/test_production_qgt.py::test_qgt_preflight_no_execution"),
("hessian_curvature_omitted","_ergonomics.py","contributions.append(_real(D[i]*second[p][q]))","contributions.append(0.)","tests/test_production_hessian.py::test_nonlinear_shared_hessian"),
("hessian_zero_gradient_prune","_ergonomics.py","if any(weights) or any(any(row) for row in second):","if any(weights):","tests/test_production_hessian.py::test_nonlinear_shared_hessian"),
("hessian_mixed_term_omitted","_ergonomics.py","weight=wi[p]*wj[q] if i==j else fsum((wi[p]*wj[q],wj[p]*wi[q]))","weight=wi[p]*wj[q]","tests/test_production_hessian.py::test_nonlinear_shared_hessian"),
("hessian_controlled_frequency","_ergonomics.py","controlled_coefficient=(1-sqrt(2))/4","controlled_coefficient=0","tests/test_production_hessian.py::test_controlled_second_frequency"),
("hessian_occurrence_cap","_ergonomics.py","if len(active)>8:","if len(active)>16:","tests/test_production_hessian.py::test_hessian_invalid_preflight"),
("hessian_shift_cap","_ergonomics.py","if len(needed)>256:","if len(needed)>1024:","tests/test_production_hessian.py::test_hessian_invalid_preflight"),
("synthesis_wrong_operator_accepted","_transpilation.py","if not float(abs(Operator(raw).data-reference.data).max())<=1e-9:","if False:","tests/test_production_native_faults.py::test_synthesis_wrong_operator_never_accepted"),
("synthesis_noncanonical_accepted","_transpilation.py","if any(item.operation.name not in (\"u\",\"cx\") for item in raw.data):","if False:","tests/test_production_native_faults.py::test_synthesis_noncanonical_output"),
("synthesis_output_cap","_transpilation.py","if len(raw.data)>10000:","if len(raw.data)>20000:","tests/test_production_native_faults.py::test_synthesis_output_limit"),
)

def read_evidence(path):
    """Only assertion/explicit pytest.fail call failures count as kills."""
    cases=[]
    try:
        root=ET.parse(path)
    except (OSError,ET.ParseError):
        return {"valid":False,"cases":[]}
    for row in root.iter("testcase"):
        identity=row.attrib.get("classname","")+"::"+row.attrib.get("name","")
        errors=row.findall("error")
        skipped=row.findall("skipped")
        failures=row.findall("failure")
        if errors:
            status="error"
        elif skipped:
            status="skipped"
        elif failures:
            status="assertion" if all(
                re.search(r": (AssertionError|Failed)\s*$",f.text or "") for f in failures
            ) else "unexpected_exception"
        else:
            status="passed"
        cases.append({"id":identity,"status":status})
    return {"valid":bool(cases) and len({x["id"] for x in cases})==len(cases),"cases":cases}

def classify(baseline,mutant):
    a,b=baseline["evidence"],mutant["evidence"]
    if not a["valid"] or baseline["exit"]!=0 or any(x["status"]!="passed" for x in a["cases"]):
        return "invalid_baseline"
    if not b["valid"] or {x["id"] for x in a["cases"]}!={x["id"] for x in b["cases"]}:
        return "invalid"
    statuses={x["status"] for x in b["cases"]}
    if mutant["exit"]==1 and statuses<={"passed","assertion"} and "assertion" in statuses:
        return "killed"
    if mutant["exit"]==0 and statuses=={"passed"}:
        return "survived"
    return "invalid"

def run_test(root,node):
    env=dict(os.environ,PYTHONPATH=str(root/"src"),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    check=subprocess.run([sys.executable,"-c","import pathlib,ketary; assert pathlib.Path(ketary.__file__).resolve().is_relative_to(pathlib.Path('src').resolve())"],cwd=root,env=env,capture_output=True,text=True,timeout=20)
    if check.returncode:raise RuntimeError("isolated import preflight failed: "+check.stderr[-1000:])
    report=root/"mutation-test.xml"
    report.unlink(missing_ok=True)
    start=time.monotonic()
    try:
        out=subprocess.run([sys.executable,"-m","pytest","-q","--import-mode=importlib",node,"--junitxml",str(report)],cwd=root,env=env,capture_output=True,text=True,timeout=120)
    except subprocess.TimeoutExpired:
        return {"exit":-1,"seconds":time.monotonic()-start,"log":"timeout","evidence":{"valid":False,"cases":[]}}
    return {"exit":out.returncode,"seconds":time.monotonic()-start,"log":(out.stdout+out.stderr)[-6000:],"evidence":read_evidence(report)}

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
        if not baseline["evidence"]["valid"] or baseline["exit"]!=0 or any(x["status"]!="passed" for x in baseline["evidence"]["cases"]):
            return dict(id=name,status="invalid_baseline",baseline=baseline)
        target.write_text(original.replace(old,new,1))
        # Avoid timestamp/size pyc reuse after a source mutation.
        for cache in root.rglob("__pycache__"):shutil.rmtree(cache)
        result=run_test(root,node)
        status=classify(baseline,result)
        return dict(id=name,status=status,source=file,node=node,baseline=baseline,mutant=result)

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    rows=[]
    for m in MUTANTS:
        try:
            row=evaluate(m)
        except (RuntimeError,OSError,subprocess.SubprocessError) as exc:
            row=dict(id=m[0],status="invalid",error=str(exc))
        rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope=f"{len(MUTANTS)} declared source mutants; not general mutation coverage",rows=rows),indent=2))
    if any(r["status"]!="killed" for r in rows):raise SystemExit(1)
if __name__=="__main__":main()
