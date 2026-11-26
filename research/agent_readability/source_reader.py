"""Static reader for a deliberately restricted, literal Python fragment.

No imports, calls, eval, exec, or arbitrary code are executed. AST locations
are UTF-8 byte offsets, zero-based columns, one-based lines.
"""
import ast
import math
_ARITY={"h":1,"x":1,"y":1,"z":1,"s":1,"sdg":1,"t":1,"tdg":1,"rx":1,"ry":1,"rz":1,"cx":2,"cz":2,"swap":2,"ccx":3}
_ROT={"rx","ry","rz"}

def read_source(source):
    def fail(reason): return {"status":"UNSUPPORTED","reason":reason}
    if not isinstance(source,str) or len(source)>8192: return fail("source limit/type")
    try:
        body=ast.parse(source).body
        if len(body)<2 or sum(1 for node in ast.walk(ast.Module(body=body,type_ignores=[])))>512:
            return fail("syntax/AST limit")
        imp,assignment,*rest=body
        if isinstance(imp,ast.Import) and len(imp.names)==1 and imp.names[0].name=="ketary" and imp.names[0].asname=="q":
            framework="ketary"
        elif isinstance(imp,ast.ImportFrom) and imp.module=="qiskit" and imp.level==0 and len(imp.names)==1 and imp.names[0].name=="QuantumCircuit" and imp.names[0].asname is None:
            framework="qiskit"
        else: return fail("unsupported import")
        if not isinstance(assignment,ast.Assign) or len(assignment.targets)!=1 or not isinstance(assignment.targets[0],ast.Name):
            return fail("constructor assignment")
        name=assignment.targets[0].id
        if name in ("q","QuantumCircuit","__builtins__"): return fail("shadowed name")
        operations=[]
        width=None
        def literal(node):
            if isinstance(node,ast.Constant) and type(node.value) in (int,float): return node.value
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)) and isinstance(node.operand,ast.Constant) and type(node.operand.value) in (int,float):
                return -node.operand.value if isinstance(node.op,ast.USub) else node.operand.value
            raise ValueError("nonliteral argument")
        def visit(expr,constructor=False):
            nonlocal width
            if not constructor and isinstance(expr,ast.Name) and expr.id==name: return
            if not isinstance(expr,ast.Call) or expr.keywords: raise ValueError("dynamic expression")
            f=expr.func
            ctor=(framework=="ketary" and isinstance(f,ast.Attribute) and f.attr=="Circuit" and isinstance(f.value,ast.Name) and f.value.id=="q") or (framework=="qiskit" and isinstance(f,ast.Name) and f.id=="QuantumCircuit")
            if ctor:
                if not constructor or width is not None or len(expr.args)!=1: raise ValueError("constructor position")
                width=literal(expr.args[0])
                if type(width) is not int or not 1<=width<=22: raise ValueError("width")
                return
            if not isinstance(f,ast.Attribute) or f.attr not in _ARITY: raise ValueError("unsupported gate")
            gate=f.attr; base=f.value
            if framework=="ketary" and isinstance(base,ast.Attribute) and base.attr=="gates": base=base.value
            if framework=="qiskit" and not (isinstance(base,ast.Name) and base.id==name):
                # Qiskit native gate calls return instruction sets, not Circuit.
                raise ValueError("unsupported native chaining")
            visit(base,constructor)
            if width is None: raise ValueError("constructor missing")
            args=[literal(a) for a in expr.args]
            if len(args)!=_ARITY[gate]+(gate in _ROT): raise ValueError("arity")
            params=args[:1] if gate in _ROT else []
            wires=args[1:] if gate in _ROT else args
            if any(type(w) is not int or not 0<=w<width for w in wires) or len(set(wires))!=len(wires): raise ValueError("wires")
            if any(not math.isfinite(v) for v in params): raise ValueError("parameter")
            operations.append({"index":len(operations)+1,"gate":gate,"wires":wires,"params":[float(p) for p in params],
                "line":f.end_lineno,"column":f.end_col_offset-len(gate),"end_column":f.end_col_offset})
            if len(operations)>64: raise ValueError("operation cap")
        visit(assignment.value,True)
        if width is None: return fail("constructor missing")
        for statement in rest:
            if not isinstance(statement,ast.Expr) or not isinstance(statement.value,ast.Call): return fail("unsupported statement")
            visit(statement.value)
        return {"status":"PASS","framework":framework,"num_qubits":width,"operations":operations,"scope":"literal fragment, zero global phase"}
    except (ValueError,TypeError,SyntaxError,OverflowError,RecursionError):
        return fail("unsupported or invalid literal fragment")
