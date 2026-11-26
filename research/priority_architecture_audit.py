"""Reproducible selected ownership/validation audit; no runtime refactor."""
import ast
import collections
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"src"/"ketary"
MODULES=("_circuit","_ergonomics","_algorithms","_transpilation","_validation","_adapter","_observable","_result")

def inventory():
    rows={}
    exact=collections.defaultdict(list)
    for name in MODULES:
        src=(ROOT/(name+".py")).read_text()
        tree=ast.parse(src)
        functions=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        relative=sorted({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.level and n.module})
        checks=[{"function":n.name,"line":n.lineno} for n in functions if any(isinstance(x,ast.Call) and ((isinstance(x.func,ast.Attribute) and x.func.attr=="isfinite") or (isinstance(x.func,ast.Name) and x.func.id in {"_real","_angle","_int","_limit","isfinite"})) for x in ast.walk(n))]
        rows[name]={"lines":len(src.splitlines()),"functions":len(functions),"relative_imports":relative,"numeric_validation_sites":checks}
        for n in functions:
            if len(n.body)<3:continue
            fingerprint=ast.dump(ast.Module(body=n.body,type_ignores=[]),include_attributes=False)
            exact[fingerprint].append({"module":name,"function":n.name,"line":n.lineno})
    return {"modules":rows,"identical_bodies":[v for v in exact.values() if len(v)>1],"decision":"identical AST bodies are candidates only; preserve distinct exception, mode and ownership contracts","scope":"selected modules, static AST, no semantic equivalence or runtime performance claim"}

if __name__=="__main__":
    print(json.dumps(inventory(),indent=2))
