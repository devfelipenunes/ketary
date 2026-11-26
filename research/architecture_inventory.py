"""Reproducible static audit of the installed SDK source, not a quality score."""
import ast
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
def inspect(root=ROOT):
    modules={p.stem:p for p in sorted((root/"src/ketary").glob("*.py"))}
    edges=set();eager=set();external=set();rows={}
    for name,path in modules.items():
        source=path.read_text();tree=ast.parse(source)
        def walk(node,local=False):
            if isinstance(node,ast.ImportFrom):
                if node.level==1 and node.module in modules:
                    edge=(name,node.module);edges.add(edge)
                    if not local:eager.add(edge)
                elif node.level==0 and node.module:
                    external.add((name,node.module.split(".")[0]))
            elif isinstance(node,ast.Import):
                for alias in node.names:external.add((name,alias.name.split(".")[0]))
            local=local or isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda))
            for child in ast.iter_child_nodes(node):walk(child,local)
        walk(tree)
        functions=[node for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
        rows[name]={"physical_lines":len(source.splitlines()),"functions":len(functions),
                    "classes":sum(isinstance(node,ast.ClassDef) for node in ast.walk(tree)),
                    "largest_functions":sorted([(node.name,node.end_lineno-node.lineno+1) for node in functions],key=lambda x:(-x[1],x[0]))[:5]}
    def components(es):
        graph={n:set() for n in modules}
        for a,b in es:graph[a].add(b)
        def reachable(n):
            seen={n};stack=[n]
            while stack:
                for child in graph[stack.pop()]-seen:
                    seen.add(child);stack.append(child)
            return seen
        reach={n:reachable(n) for n in graph}
        unseen=set(graph);out=[]
        while unseen:
            n=min(unseen);part=sorted(x for x in reach[n] if n in reach[x]);unseen.difference_update(part)
            if len(part)>1 or (n,n) in es:out.append(part)
        return sorted(out)
    return {"scope":"static explicit AST imports; no dynamic import resolution or runtime dependency guarantee",
            "modules":len(modules),"physical_lines":sum(v["physical_lines"] for v in rows.values()),
            "internal_edges":len(edges),"eager_edges":len(eager),"cycles":components(edges),"eager_cycles":components(eager),
            "module_stats":rows,"internal_imports":sorted(edges),"external_imports":sorted(external)}
if __name__=="__main__":print(json.dumps(inspect(),indent=2))
