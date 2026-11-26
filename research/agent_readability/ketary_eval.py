"""KetaryEval research harness: offline, no arbitrary source execution.

The checked-in cases are public calibration examples, not a hidden benchmark.
Generated code is interpreted only through source_reader and a gate allowlist.
"""
import argparse
import ast
import io
import json
import tokenize
import random
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from source_reader import read_source

FRAMEWORKS=("qiskit","ketary","candidate")
# Tuples use native ordered gate arguments, angles in radians.
CASES=[
 {"id":"G01","kind":"generation","n":2,"request":"Prepare the Bell state (|00>+|11>)/sqrt(2) with H on wire 0 and CX 0->1.","gates":[("h",0),("cx",0,1)],"mutant":[("h",0),("cx",1,0)]},
 {"id":"G02","kind":"generation","n":3,"request":"Apply X on wire 2 and controlled-X with control 2 and target 0. Preserve all other wires.","gates":[("x",2),("cx",2,0)],"mutant":[("x",2),("cx",0,2)]},
 {"id":"G03","kind":"generation","n":1,"request":"Apply RY(0.37), then its exact inverse, both on wire 0. Use both gates.","gates":[("ry",.37,0),("ry",-.37,0)],"mutant":[("ry",.37,0),("ry",.37,0)],"count":2},
 {"id":"G04","kind":"generation","n":3,"request":"Prepare GHZ by H(0), CX(0,1), CX(1,2), preserving relative phase.","gates":[("h",0),("cx",0,1),("cx",1,2)],"mutant":[("h",0),("cx",0,1),("cx",1,2),("z",0)]},
 {"id":"C01","kind":"comprehension","n":3,"request":"Return the gate names and ordered wire lists for the code. Exclude angles from wire lists.","source":[("h",2),("cx",2,0),("ry",.4,1)],"answer":[["h",[2]],["cx",[2,0]],["ry",[1]]],"wrong":[["h",[2]],["cx",[0,2]],["ry",[1]]]},
 {"id":"C02","kind":"comprehension","n":2,"request":"Compare this circuit to H(0), CX(0,1). Do their Z-basis distributions match? Are their output states equivalent up to global phase? Return [same_distribution,same_state] as booleans.","source":[("h",0),("cx",0,1),("z",0)],"answer":[True,False],"wrong":[True,True]},
 {"id":"C03","kind":"comprehension","n":3,"request":"Starting in |000>, return the only measurement label with nonzero probability. Use highest-wire-first ordering.","source":[("x",0),("x",2),("cx",2,1)],"answer":"111","wrong":"101"},
 {"id":"C04","kind":"comprehension","n":2,"request":"Can the restricted literal reader establish the circuit without knowing theta? Return the string UNSUPPORTED if not.","dynamic":True,"answer":"UNSUPPORTED","wrong":"PASS"},
 {"id":"R01","kind":"repair","n":2,"request":"Fix the circuit so the full operator is H on 0 followed by CX 0->1.","source":[("h",0),("cx",1,0)],"gates":[("h",0),("cx",0,1)],"mutant":[("h",0),("cx",1,0)]},
 {"id":"R02","kind":"repair","n":2,"request":"Remove the relative phase error so the full operator is H(0), CX(0,1).","source":[("h",0),("cx",0,1),("z",0)],"gates":[("h",0),("cx",0,1)],"mutant":[("h",0),("cx",0,1),("z",0)]},
 {"id":"R03","kind":"repair","n":1,"request":"Change only the second RX angle so the two gates cancel with strict global phase.","source":[("rx",.6,0),("rx",.6,0)],"gates":[("rx",.6,0),("rx",-.6,0)],"mutant":[("rx",.6,0),("rx",.6,0)],"count":2},
 {"id":"D01","kind":"diagnosis","n":2,"request":"Reference: H(0), CX(0,1), X(0). For observed code return the first divergent zero-input checkpoint (initial index 0), and actual gate name, as [index,gate].","source":[("h",0),("cx",0,1),("z",0)],"answer":[3,"z"],"wrong":[2,"cx"]},
]
def source(framework,n,gates):
    if framework=="qiskit":
        lines=["from qiskit import QuantumCircuit",f"c = QuantumCircuit({n})"]
        prefix="c."
    else:
        lines=["import ketary as q",f"c = q.Circuit({n})"]
        prefix="c.gates." if framework=="ketary" else "c."
    for name,*args in gates:
        lines.append(prefix+name+"("+", ".join(repr(a) for a in args)+")")
    return "\n".join(lines)

def prompt(case,framework,condition='card'):
    p={"id":case["id"],"kind":case["kind"],"framework":framework,"request":case["request"],
       "response_schema":{"code":"Python source string"} if "gates" in case else {"answer":"requested JSON value"}}
    if "source" in case: p["source"]=source(framework,case["n"],case["source"])
    if case.get("dynamic"): p["source"]=source(framework,case["n"],[])+("\nc.gates.rx(theta, 0)" if framework=="ketary" else "\nc.rx(theta, 0)")
    if "gates" in case:
        p["constraints"]="Use exactly the literal constructor/import and gate statements of the requested API; no loops, variables, helper functions, extra imports or symbolic arguments. Circuit must implement the specified full operator with strict global phase. Return JSON only."
        if condition!="none": p["api"]={"constructor":"QuantumCircuit(n)" if framework=="qiskit" else "q.Circuit(n)","gate_prefix":"c.gates." if framework=="ketary" else "c.","import":"from qiskit import QuantumCircuit" if framework=="qiskit" else "import ketary as q"}
    if condition not in ("none","card","reference"): raise ValueError("invalid documentation condition")
    if condition!="none":
        p["context"]={"bit_order":"highest-wire-first","rotation_unit":"radian","cx_arguments":"control,target",
            "scope":"ideal unitary logical circuits; initial state all zero"}
    if condition=="reference":
        p["reference"]={
            "construction":"Construct one circuit with n qubits; use only literal supported gate calls.",
            "gates":"h,x,y,z,s,sdg,t,tdg(wire); rx,ry,rz(angle,wire); cx,cz,swap(wire,wire); ccx(control,control,target)",
            "measurement":"Z-basis probabilities discard relative phase; equal distributions need not imply equal states.",
            "equivalence":"Global phase may be ignored for states only when requested; full operator checks in this benchmark preserve it.",
            "checkpoints":"Index zero is before any gate; subsequent indices follow ordered operations.",
            "source":"The literal reader cannot resolve dynamic expressions or unknown variables. Abstain rather than infer.",
            "mutation":"Gate calls append operations; use explicit statements in the submitted code."
        }
    return p

def native(n,gates):
    c=QuantumCircuit(n)
    for name,*args in gates: getattr(c,name)(*args)
    return c

def grade(case,framework,response):
    if type(response) is not dict: return {"status":"INVALID","reason":"expected object"}
    if "gates" not in case:
        if set(response)!={"answer"}: return {"status":"INVALID","reason":"answer schema"}
        try:
            equal=json.dumps(response["answer"],sort_keys=True,allow_nan=False)==json.dumps(case["answer"],sort_keys=True)
        except (ValueError,TypeError): return {"status":"INVALID","reason":"invalid answer"}
        return {"status":"PASS" if equal else "FAIL","reason":"exact structured answer"}
    if set(response)!={"code"} or not isinstance(response["code"],str): return {"status":"INVALID","reason":"code schema"}
    report=read_source(response["code"])
    if report["status"]!="PASS": return {"status":"UNSUPPORTED","reason":report["reason"]}
    expected_framework="qiskit" if framework=="qiskit" else "ketary"
    if report["framework"]!=expected_framework: return {"status":"FAIL","reason":"wrong API"}
    if framework=="ketary":
        for node in ast.walk(ast.parse(response["code"])):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr!="Circuit":
                base=node.func.value
                if not isinstance(base,ast.Attribute) or base.attr!="gates": return {"status":"FAIL","reason":"research alias not in baseline"}
    if report["num_qubits"]!=case["n"]: return {"status":"FAIL","reason":"qubit count"}
    if "count" in case and len(report["operations"])!=case["count"]: return {"status":"FAIL","reason":"gate count"}
    # Rebuild the allowlisted operations, never execute the submitted program.
    gates=[(op["gate"],*op["params"],*op["wires"]) for op in report["operations"]]
    if case['id'] in ('G03','R03') and gates!=case['gates']:
        return {'status':'FAIL','reason':'requested literal rotation sequence'}
    actual=Operator(native(case["n"],gates)).data
    expected=Operator(native(case["n"],case["gates"])).data
    return {"status":"PASS" if np.allclose(actual,expected,atol=1e-9,rtol=0) else "FAIL","reason":"strict full operator"}

def reference(case,framework,mutant=False):
    if "gates" in case: return {"code":source(framework,case["n"],case["mutant" if mutant else "gates"])}
    return {"answer":case["wrong" if mutant else "answer"]}

def self_test():
    rows=[]
    for framework in FRAMEWORKS:
        for case in CASES:
            good=grade(case,framework,reference(case,framework))
            bad=grade(case,framework,reference(case,framework,True))
            assert good["status"]=="PASS",(case["id"],framework,good)
            assert bad["status"]=="FAIL",(case["id"],framework,bad)
            rows.append({"id":case["id"],"framework":framework,"reference":good["status"],"mutant":bad["status"]})
    return {"cases":len(CASES),"reference_pass":len(rows),"mutants_rejected":len(rows),"note":"authored calibration fixtures, not independent LLM trials","rows":rows}

def lexical(code):
    excluded={tokenize.ENCODING,tokenize.ENDMARKER,tokenize.NEWLINE,tokenize.NL,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT}
    return sum(t.type not in excluded for t in tokenize.generate_tokens(io.StringIO(code).readline))

def compare_syntax():
    rows=[]
    for case in CASES:
        if "gates" not in case: continue
        # Compare equivalent snippets using the same construction style.
        variants={f:source(f,case["n"],case["gates"]) for f in FRAMEWORKS}
        rows.append({"id":case["id"],**{f:lexical(v) for f,v in variants.items()}})
    return {"rows":rows,"totals":{f:sum(row[f] for row in rows) for f in FRAMEWORKS},"unit":"Python lexical tokens, not model tokens"}

def main():
    parser=argparse.ArgumentParser()
    options=parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--prompts",choices=FRAMEWORKS)
    options.add_argument("--grade",type=Path)
    options.add_argument("--self-test",action="store_true")
    options.add_argument("--compare-syntax",action="store_true")
    parser.add_argument('--condition',choices=['none','card','reference'],default='card')
    parser.add_argument('--seed',type=int,default=42)
    args=parser.parse_args()
    if args.self_test: out=self_test()
    elif args.compare_syntax: out=compare_syntax()
    elif args.prompts:
        out=[prompt(c,args.prompts,args.condition) for c in CASES]
        random.Random(args.seed).shuffle(out)
    else:
        if args.grade.stat().st_size>1024*1024: raise ValueError("response file too large")
        responses=json.loads(args.grade.read_text())
        if type(responses) is not list or len(responses)>10000: raise ValueError("invalid response list")
        by_id={c["id"]:c for c in CASES}; out=[]
        for row in responses:
            if type(row) is not dict or row.get("id") not in by_id or row.get("framework") not in FRAMEWORKS: raise ValueError("invalid case metadata")
            out.append({"id":row["id"],"framework":row["framework"],**grade(by_id[row["id"]],row["framework"],row.get("response"))})
    print(json.dumps(out,indent=2,allow_nan=False))
if __name__=="__main__": main()
