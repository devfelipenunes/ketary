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
("synthesis_output_cap","_transpilation.py","if len(raw.data)>10000:","if len(raw.data)>20000:","tests/test_production_native_faults.py::test_synthesis_output_limit_isolated"),
("local_channel_wrong_wire_order","_classical.py","result=state.evolve(owned,qargs=list(selected))","result=state.evolve(owned,qargs=list(reversed(selected)))","tests/test_production_local_channels.py::test_local_channel_dense_oracle"),
("local_channel_ignored","_classical.py","result=state.evolve(owned,qargs=list(selected))","result=state","tests/test_production_local_channels.py::test_local_channel_dense_oracle"),
("replay_duplicate_key","_replay.py","if key in out:","if False:","tests/test_production_semantic_mutants.py::test_replay_duplicate_key"),
("replay_extra_field","_replay.py","set(value)!=set(expected)","not set(expected)<=set(value)","tests/test_production_semantic_mutants.py::test_replay_unknown_field"),
("replay_schema_version","_replay.py","data[\"schema_version\"]!=_SCHEMA","False","tests/test_production_semantic_mutants.py::test_replay_unknown_schema"),
("replay_boolean_schema","_replay.py","type(data[\"schema_version\"]) is not int","not isinstance(data[\"schema_version\"],int)","tests/test_production_semantic_mutants.py::test_replay_boolean_schema"),
("replay_producer_length","_replay.py","len(v)>100","len(v)>1000","tests/test_production_semantic_mutants.py::test_replay_producer_cap"),
("replay_width_cap","_replay.py","_MAX_QUBITS=22","_MAX_QUBITS=23","tests/test_production_semantic_mutants.py::test_replay_width_cap"),
("replay_gate_cap","_replay.py","_MAX_GATES=10000","_MAX_GATES=10001","tests/test_production_semantic_mutants.py::test_replay_gate_cap"),
("replay_byte_cap","_replay.py","_MAX_BYTES=1024*1024","_MAX_BYTES=2*1024*1024","tests/test_production_semantic_mutants.py::test_replay_byte_cap"),
("replay_phase_lost","_replay.py","qc=QC(n,global_phase=phase)","qc=QC(n,global_phase=0)","tests/test_production_semantic_mutants.py::test_replay_strict_phase"),
("replay_reverse_wire_order","_replay.py","getattr(qc,name)(*params,*wires)","getattr(qc,name)(*params,*reversed(wires))","tests/test_production_semantic_mutants.py::test_replay_control_target_order"),
("replay_angle_absolute","_replay.py","tuple(_angle(p) for p in params)","tuple(abs(_angle(p)) for p in params)","tests/test_production_semantic_mutants.py::test_replay_negative_rotation"),
("int_accepts_bool","_validation.py","if isinstance(value, (bool, np.bool_)):","if False:","tests/test_production_semantic_mutants.py::test_bool_integer_rejected"),
("real_accepts_bool","_validation.py","if isinstance(value,(bool,np.bool_)) or not isinstance(value,Real):\n        raise ValueError(\"expected a finite real number\")","if not isinstance(value,Real):\n        raise ValueError(\"expected a finite real number\")","tests/test_production_semantic_mutants.py::test_bool_real_rejected"),
("angle_accepts_bool","_validation.py","if isinstance(value,(bool,np.bool_)) or not isinstance(value,Real):\n        raise ValueError(\"rotation angle must be a finite real number in radians\")","if not isinstance(value,Real):\n        raise ValueError(\"rotation angle must be a finite real number in radians\")","tests/test_production_semantic_mutants.py::test_bool_angle_rejected"),
("payload_budget_bypass","_validation.py","if n > 62 or 16 * (1 << n) * snapshots > budget:","if n > 62:","tests/test_production_semantic_mutants.py::test_payload_preflight"),
("pauli_mapping_endianness","_validation.py","label[n-1-wire]=axis","label[wire]=axis","tests/test_production_semantic_mutants.py::test_pauli_mapping_order"),
("operator_width_false_pass","_checks.py","return CheckResult(\"FAIL\",None,None,t,\"different qubit counts\")","return CheckResult(\"PASS\",None,None,t,\"different qubit counts\")","tests/test_production_semantic_mutants.py::test_operator_width_fail"),
("operator_budget_false_pass","_checks.py","return CheckResult(\"UNSUPPORTED\",None,None,t,\"operator payload or eight-qubit limit exceeded\")","return CheckResult(\"PASS\",None,None,t,\"operator payload or eight-qubit limit exceeded\")","tests/test_production_semantic_mutants.py::test_operator_budget_unsupported"),
("operator_phase_default","_checks.py","def equivalent(self,other,*,ignore_global_phase=False","def equivalent(self,other,*,ignore_global_phase=True","tests/test_production_semantic_mutants.py::test_operator_default_strict_phase"),
("conditional_denominator_lost","_result.py","mass(g|e)/denominator","mass(g|e)","tests/test_production_semantic_mutants.py::test_conditional_mass_normalization"),
("conditional_conflict_false_one","_result.py","if any(w in g and g[w]!=b for w,b in e.items()):\n            return 0.0","if any(w in g and g[w]!=b for w,b in e.items()):\n            return 1.0","tests/test_production_semantic_mutants.py::test_conditional_conflicting_events"),
("trace_distance_squared","_result.py","math.sqrt(max(0.0,1-self.fidelity(target)))","max(0.0,1-self.fidelity(target))","tests/test_production_semantic_mutants.py::test_pure_trace_distance"),
("top_tie_order","_result.py","key=lambda i:(abs(data[i])**2,-i)","key=lambda i:(abs(data[i])**2,i)","tests/test_production_semantic_mutants.py::test_top_probability_ties"),
("pauli_variance_wrong_power","_result.py","return max(0.0,1-expectation**2)","return max(0.0,1-expectation)","tests/test_production_semantic_mutants.py::test_pauli_variance_square"),
("entropy_natural_log","_result.py","return float(-np.sum(p*np.log2(p)))","return float(-np.sum(p*np.log(p)))","tests/test_production_semantic_mutants.py::test_entropy_base_two"),
("statistical_unmeasured_false_pass","_statistical.py","return {\"status\":\"UNSUPPORTED\",\"reason\":\"not all classical bits were measured\"}","return {\"status\":\"PASS\",\"reason\":\"not all classical bits were measured\"}","tests/test_production_semantic_mutants.py::test_statistical_unmeasured_unsupported"),
("statistical_union_bound_lost","_statistical.py","math.log(2*len(self.probabilities)/(1-self.confidence))","math.log(2/(1-self.confidence))","tests/test_production_semantic_mutants.py::test_statistical_union_bound"),
("statistical_overlap_false_pass","_statistical.py","else \"INCONCLUSIVE\"\n            rows[label]","else \"PASS\"\n            rows[label]","tests/test_production_semantic_mutants.py::test_statistical_overlap_inconclusive"),
("statistical_shot_total_ignored","_statistical.py","or sum(counts.values())!=shots:","or False:","tests/test_production_semantic_mutants.py::test_statistical_bad_total_rejected"),
("contract_failure_false_pass","_contracts.py","status=\"FAIL\" if \"FAIL\" in statuses","status=\"PASS\" if \"FAIL\" in statuses","tests/test_production_semantic_mutants.py::test_contract_failure_precedence"),
("optimize_cross_wire_cancellation","_optimization.py","if a.qubits!=b.qubits:","if False:","tests/test_production_semantic_mutants.py::test_optimize_different_wires"),
("optimize_modulo_phase_loss","_optimization.py","return float(x.params[0])==-float(y.params[0])","return (float(x.params[0])+float(y.params[0]))%(2*__import__('math').pi)==0","tests/test_production_semantic_mutants.py::test_optimize_rotation_phase_strict"),
("result_norm_guard_removed","_result.py","or not math.isclose(norm_sq,1,rel_tol=0,abs_tol=1e-9):","or False:","tests/test_production_semantic_mutants.py::test_result_rejects_unnormalized"),
("result_caller_alias","_result.py","self._data = a if take_ownership else a.copy()","self._data = a","tests/test_production_semantic_mutants.py::test_result_caller_ownership"),
("annotation_source_alias","_adapter.py","source=template.copy()","source=template","tests/test_production_annotated_projection.py::test_annotated_projection_structural_and_math"),
("annotation_source_metadata_lost","_adapter.py","source=template.copy()","source=template.copy();source.metadata={}","tests/test_production_annotated_projection.py::test_annotated_projection_structural_and_math"),
("annotation_source_barrier_lost","_adapter.py","source=template.copy()","source=template.copy();source.data=[item for item in source.data if type(item.operation) is not Barrier]","tests/test_production_annotated_projection.py::test_annotated_projection_structural_and_math"),
("annotation_projection_phase_lost","_adapter.py","logical=QC(source.num_qubits,global_phase=source.global_phase)","logical=QC(source.num_qubits,global_phase=0)","tests/test_production_annotated_projection.py::test_annotated_projection_structural_and_math"),
("annotation_projection_wire_order","_adapter.py","logical.append(item.operation,[source.find_bit(w).index for w in item.qubits],copy=True)","logical.append(item.operation,[source.find_bit(w).index for w in reversed(item.qubits)],copy=True)","tests/test_production_annotated_projection.py::test_annotated_projection_structural_and_math"),
("annotation_depth_bypass","_adapter.py","if nodes>4096 or depth>8:","if nodes>4096:","tests/test_production_annotated_projection.py::test_metadata_budgets[deep]"),
("annotation_string_cap","_adapter.py","if len(value)>4096:","if len(value)>8192:","tests/test_production_annotated_projection.py::test_metadata_budgets[string]"),
("annotation_integer_cap","_adapter.py","if value.bit_length()>64:","if value.bit_length()>128:","tests/test_production_annotated_projection.py::test_metadata_budgets[integer]"),
("annotation_byte_cap","_adapter.py","if len(json.dumps(metadata,ensure_ascii=False,allow_nan=False,separators=(\",\",\":\")).encode(\"utf-8\"))>65536:","if False:","tests/test_production_annotated_projection.py::test_metadata_budgets[bytes]"),
("strict_import_metadata_bypass","_adapter.py","or getattr(qc,\"layout\",None) is not None or qc.metadata:","or getattr(qc,\"layout\",None) is not None:","tests/test_production_final_mutants.py::test_strict_metadata"),
("local_channel_budget_bypass","_classical.py","if 16*(3*(1<<(2*n))+len(matrices)*(1<<(2*width)))>max_bytes:","if False:","tests/test_production_local_channels.py::test_local_channel_budget_and_invalid_before_execution"),
("full_channel_width_bypass","_classical.py","if n>4:\n            raise ResourceLimit(\"full-width Kraus channel execution supports <=4 wires\")","if False:\n            raise ResourceLimit(\"full-width Kraus channel execution supports <=4 wires\")","tests/test_production_final_mutants.py::test_full_channel_width"),
("invalid_density_output_accepted","_classical.py","if not out.is_valid(atol=1e-9,rtol=0):","if False:","tests/test_production_native_faults.py::test_native_density_invalid_result"),
("invalid_channel_output_accepted","_classical.py","if result.num_qubits!=n or not result.is_valid(atol=1e-9,rtol=0):","if result.num_qubits!=n:","tests/test_production_native_faults.py::test_channel_invalid_backend_result"),
("density_input_guard_bypass","_classical.py","if not initial_state.is_valid(atol=1e-9,rtol=0):","if False:","tests/test_production_final_mutants.py::test_density_input_preflight"),
("density_width_bypass","_classical.py","if n>8 or len(circuit._qc.data)>1024:","if len(circuit._qc.data)>1024:","tests/test_production_final_mutants.py::test_density_width_preflight"),
("shot_provenance_swapped","_classical.py","measurements=tuple((i+1,qc.find_bit(item.qubits[0]).index,qc.find_bit(item.clbits[0]).index)","measurements=tuple((i+1,qc.find_bit(item.clbits[0]).index,qc.find_bit(item.qubits[0]).index)","tests/test_production_final_mutants.py::test_shot_provenance"),
("conditional_measurement_bypass","_classical.py","elif depth==0 and getattr(op,\"base_class\",None) in (Measure,Reset):","elif getattr(op,\"base_class\",None) in (Measure,Reset):","tests/test_production_nested_dynamic.py::test_nested_forbidden_leaves_even_in_unreachable_branch[measure]"),
("shot_cap_bypass","_classical.py","if shots>10000 or qc.num_qubits>12 or qc.num_clbits>12 or len(qc.data)>1024:","if qc.num_qubits>12 or qc.num_clbits>12 or len(qc.data)>1024:","tests/test_production_final_mutants.py::test_shot_cap"),
("shot_missing_measurement","_classical.py","if not any(item.operation.name==\"measure\" for item in qc.data):","if False:","tests/test_production_final_mutants.py::test_shot_requires_measurement"),
("dense_evolution_time_sign","_transpilation.py","HamiltonianGate(H,t)","HamiltonianGate(H,-t)","tests/test_production_final_mutants.py::test_dense_evolution_sign"),
("dense_state_conjugation","_transpilation.py","StatePreparation(list(values),normalize=False)","StatePreparation([v.conjugate() for v in values],normalize=False)","tests/test_production_final_mutants.py::test_dense_state_phase"),
("dense_unitary_adjoint","_transpilation.py","UnitaryGate(operator)","UnitaryGate(operator.adjoint())","tests/test_production_final_mutants.py::test_dense_unitary_direction"),
("control_state_forced_closed","_transpilation.py","ctrl_state=state,annotated=False","ctrl_state=(1<<controls)-1,annotated=False","tests/test_production_final_mutants.py::test_open_control"),
("synthesis_input_cap","_transpilation.py","if not 1<=template.num_qubits<=5 or len(template.data)>256:","if not 1<=template.num_qubits<=5:","tests/test_production_final_mutants.py::test_synthesis_input_cap"),
("observable_embedding_axis_order","_observable.py","axes[n-1-w]=label[k-1-i]","axes[n-1-w]=label[i]","tests/test_production_final_mutants.py::test_asymmetric_embedding"),
("observable_add_sign","_observable.py","result[label]=_real(result.get(label,0.0)+value)","result[label]=_real(result.get(label,0.0)-value)","tests/test_production_final_mutants.py::test_observable_addition"),
("overlapping_tensor_accepted","_observable.py","if support(left)&support(right):","if False:","tests/test_production_final_mutants.py::test_overlapping_tensor"),
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
