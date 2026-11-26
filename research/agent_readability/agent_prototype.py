"""Research-only adapters. No production API change; no model/network calls."""
from dataclasses import asdict
from itertools import islice
import ast
import math
import ketary as q

def inspect_circuit(circuit, *, max_operations=32):
    if type(max_operations) is not int or not 1<=max_operations<=256:
        raise ValueError("operation cap must be 1..256")
    raw=circuit.to_qiskit()  # full native copy: a known prototype cost
    operations=[{"index":i+1,"gate":item.operation.name,
        "wires":[raw.find_bit(w).index for w in item.qubits],
        "params":[float(p) for p in item.operation.params]}
        for i,item in enumerate(islice(raw.data,max_operations))]
    return {"num_qubits":raw.num_qubits,"global_phase":float(raw.global_phase),
        "gate_count":len(raw.data),"bit_order":"highest-wire-first",
        "operations":operations,"omitted":len(raw.data)-len(operations)}

def evidence(result, *, bits, paulis=()):
    bits=list(islice(iter(bits),33)); paulis=list(islice(iter(paulis),33))
    if len(bits)>32 or len(paulis)>32: raise ValueError("evidence cap exceeded")
    amplitudes={}
    probabilities={}
    for label in bits:
        a=result.math.amplitude(label)
        amplitudes[label]=[a.real,a.imag]
        probabilities[label]=result.math.probability(label)
    return {"num_qubits":result.num_qubits,"probabilities":probabilities,
        "amplitudes":amplitudes,"expectations":{p:result.math.expectation(p) for p in paulis},
        "norm":result.math.norm(),"scope":"ideal pure-state snapshot"}

def checks(**named):
    if len(named)>32: raise ValueError("check cap exceeded")
    records={key:asdict(value) for key,value in named.items()}
    statuses=[v["status"] for v in records.values()]
    return {"status":"FAIL" if "FAIL" in statuses else "UNSUPPORTED" if "UNSUPPORTED" in statuses else "PASS" if statuses else "UNSUPPORTED","checks":records}

_ARITY={"h":1,"x":1,"y":1,"z":1,"s":1,"sdg":1,"t":1,"tdg":1,"rx":1,"ry":1,"rz":1,"cx":2,"cz":2,"swap":2,"ccx":3}
_ROT={"rx","ry","rz"}

def read_literal_source(source):
    """Deliberately narrow AST experiment, never executes source.

    Only canonical literal q.Circuit assignment and gate statements.
    Unsupported syntax fails closed; not a Python analyzer or new language.
    """
    def unsupported(reason):
        return {"status":"UNSUPPORTED","reason":reason}
    if not isinstance(source,str) or len(source)>8192:
        return unsupported("source size/type")
    try:
        tree=ast.parse(source)
        if sum(1 for _ in ast.walk(tree))>512:
            return unsupported("AST size")
        body=tree.body
        if body and isinstance(body[0],ast.Import):
            names=body.pop(0).names
            if len(names)!=1 or names[0].name!="ketary" or names[0].asname!="q":
                return unsupported("import")
        if not body or not isinstance(body[0],ast.Assign):
            return unsupported("constructor")
        first=body[0]
        if len(first.targets)!=1 or not isinstance(first.targets[0],ast.Name):
            return unsupported("assignment")
        name=first.targets[0].id
        call=first.value
        if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Attribute) or call.func.attr!="Circuit" or not isinstance(call.func.value,ast.Name) or call.func.value.id!="q" or call.keywords or len(call.args)!=1:
            return unsupported("constructor")
        n=ast.literal_eval(call.args[0])
        if type(n) is not int or not 1<=n<=22: return unsupported("width")
        operations=[]
        def visit(expr):
            if isinstance(expr,ast.Name) and expr.id==name: return
            if not isinstance(expr,ast.Call) or expr.keywords or not isinstance(expr.func,ast.Attribute):
                raise ValueError("dynamic syntax")
            gate=expr.func.attr
            base=expr.func.value
            if gate not in _ARITY or not isinstance(base,ast.Attribute) or base.attr!="gates":
                raise ValueError("unsupported operation")
            visit(base.value)
            args=[ast.literal_eval(a) for a in expr.args]
            if len(args)!=_ARITY[gate]+(gate in _ROT):
                raise ValueError("arity")
            params=args[:1] if gate in _ROT else []
            wires=args[1:] if gate in _ROT else args
            if any(type(w) is not int or not 0<=w<n for w in wires) or len(set(wires))!=len(wires):
                raise ValueError("wires")
            if any(type(p) not in (int,float) or not math.isfinite(p) for p in params):
                raise ValueError("params")
            operations.append({"index":len(operations)+1,"gate":gate,"wires":wires,"params":params,"line":expr.lineno,"column":expr.col_offset})
        for statement in body[1:]:
            if not isinstance(statement,ast.Expr): return unsupported("non-expression statement")
            visit(statement.value)
        return {"status":"PASS","num_qubits":n,"operations":operations}
    except (ValueError,TypeError,OverflowError,SyntaxError,RecursionError):
        return unsupported("unsupported or invalid literal syntax")
