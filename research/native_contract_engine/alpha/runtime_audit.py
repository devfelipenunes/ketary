"""Audit the installed runtime closure directly in a wheel (no imports)."""
import ast,json,pathlib,sys,zipfile
def audit(wheel):
    with zipfile.ZipFile(wheel) as z:
        mods={n.removeprefix("qcontract/_core/").removesuffix(".py"):z.read(n) for n in z.namelist()
              if n.startswith("qcontract/_core/") and n.endswith(".py") and not n.endswith("/__init__.py")}
        edges={k:sorted({v.module for v in ast.walk(ast.parse(s)) if isinstance(v,ast.ImportFrom) and v.level==1 and v.module in mods}) for k,s in mods.items()}
        roots=sorted({v.module.split(".")[-1] for v in ast.walk(ast.parse(z.read("qcontract/__init__.py"))) if isinstance(v,ast.ImportFrom) and v.level==1 and v.module and v.module.startswith("_core.")})
        assert set(roots)<=set(mods)
        seen=set(roots);todo=list(roots)
        while todo:
            for v in edges[todo.pop()]:
                if v not in seen:seen.add(v);todo.append(v)
        deferred=[]
        for k,s in mods.items():
            tree=ast.parse(s)
            for node in tree.body:
                if isinstance(node,ast.Import):assert all(v.name!="ketary" for v in node.names)
                if isinstance(node,ast.ImportFrom):assert node.module!="ketary"
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    for v in node.names:
                        if v.name=="ketary":deferred.append({"module":k,"line":node.lineno})
        return {"modules":len(mods),"lines":sum(len(v.splitlines()) for v in mods.values()),"roots":roots,"edges":edges,
                "edge_count":sum(map(len,edges.values())),"unreachable":sorted(set(mods)-seen),"legacy_imports":deferred,
                "scope":"conservative syntactic reachability including deferred imports; not runtime usage proof or removal authorization"}
if __name__=="__main__":print(json.dumps(audit(sys.argv[1]),indent=2))
