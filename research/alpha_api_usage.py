"""Repository-authored usage candidates and stub declarations, not telemetry."""
import ast,json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def inventory(root=ROOT):
    surface=json.loads((root/"docs/api-surface.json").read_text())
    life=json.loads((root/"docs/api-lifecycle.json").read_text())["entries"]
    policy=json.loads((root/"docs/api-decisions.json").read_text())
    declared=defaultdict(list)
    stub=ast.parse((root/"src/ketary/__init__.pyi").read_text())
    def walk(body,prefix=""):
        for node in body:
            if isinstance(node,ast.ClassDef):
                declared[prefix+node.name].append("class "+node.name)
                walk(node.body,prefix+node.name+".")
            elif isinstance(node,ast.FunctionDef):
                sig=ast.unparse(node.args)
                result=ast.unparse(node.returns) if node.returns else None
                declared[prefix+node.name].append(dict(signature=sig,returns=result,decorators=[ast.unparse(x) for x in node.decorator_list]))
            elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):
                declared[prefix+node.target.id].append(dict(annotation=ast.unparse(node.annotation)))
    walk(stub.body)
    direct=Counter();members=Counter();sites=defaultdict(set)
    files=[]
    for directory in ("examples","research","tests","tests_dynamic"):
        for p in sorted((root/directory).rglob("*.py")):
            if p.name in ("alpha_api_usage.py","test_alpha_four_closure.py"):continue
            files.append(p.relative_to(root).as_posix())
            tree=ast.parse(p.read_text())
            aliases={a.asname or a.name for x in ast.walk(tree) if isinstance(x,ast.Import) for a in x.names if a.name=="ketary"}
            imported={a.asname or a.name:a.name for x in ast.walk(tree) if isinstance(x,ast.ImportFrom) and x.module=="ketary" for a in x.names}
            def chain(n):
                if isinstance(n,ast.Name):return [n.id]
                if isinstance(n,ast.Attribute):
                    prefix=chain(n.value)
                    if prefix:return prefix+[n.attr]
                return []
            for node in ast.walk(tree):
                if isinstance(node,ast.Attribute):
                    members[node.attr]+=1
                    parts=chain(node)
                    if len(parts)>1 and parts[0] in aliases:
                        name=".".join(parts[1:]);direct[name]+=1;sites[name].add(files[-1])
                    elif len(parts)>1 and parts[0] in imported:
                        name=".".join([imported[parts[0]],*parts[1:]]);direct[name]+=1;sites[name].add(files[-1])
                elif isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load) and node.id in imported:
                    name=imported[node.id];direct[name]+=1;sites[name].add(files[-1])
    rows=[]
    for category,names in surface.items():
        for name in names:
            rows.append(dict(symbol=name,category=category,lifecycle=life[name],stub_declarations=declared.get(name,[]),
                direct_syntactic_references=direct[name],direct_files=sorted(sites[name]),
                untyped_member_candidates=members[name.rsplit(".",1)[-1]] if "." in name else None))
    return dict(scope="authored source AST only: syntactic import aliases may be shadowed; untyped member candidates can belong to other classes or libraries; no user telemetry, type inference, dead-code or dynamic-dispatch claims",files=len(files),categories={k:len(v) for k,v in surface.items()},rows=rows,decisions=[dict(id=x["id"],decision=x["decision"],canonical=x.get("canonical"),rationale=x["rationale"]) for x in policy["candidates"]])

if __name__=="__main__":
    print(json.dumps(inventory(),indent=2,allow_nan=False))
