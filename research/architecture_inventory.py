"""Reproducible static audit of the installed SDK source, not a quality score."""
import ast
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
def inspect(root=ROOT):
    modules={p.stem:p for p in sorted((root/"src/ketary").glob("*.py"))}
    edges=set();eager=set();external=set();rows={};local_sites=[];bodies={}
    for name,path in modules.items():
        source=path.read_text();tree=ast.parse(source)
        def walk(node,local=False):
            if isinstance(node,ast.ImportFrom):
                if node.level==1 and node.module in modules:
                    edge=(name,node.module);edges.add(edge)
                    if not local:eager.add(edge)
                    else:local_sites.append(dict(source=name,target=node.module,line=node.lineno,
                                                 symbols=sorted(alias.name for alias in node.names)))
                elif node.level==0 and node.module:
                    external.add((name,node.module.split(".")[0]))
            elif isinstance(node,ast.Import):
                for alias in node.names:external.add((name,alias.name.split(".")[0]))
            local=local or isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda))
            for child in ast.iter_child_nodes(node):walk(child,local)
        walk(tree)
        functions=[node for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
        for fn in functions:
            body=fn.body
            if body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str):
                body=body[1:]
            # Exact AST body repetition is an audit signal, not evidence of semantic equivalence.
            if len(body)>=2:
                key=ast.dump(ast.Module(body=body,type_ignores=[]),include_attributes=False)
                bodies.setdefault(key,[]).append(dict(module=name,function=fn.name,line=fn.lineno))
        rows[name]={"physical_lines":len(source.splitlines()),"functions":len(functions),
                    "branch_nodes":sum(isinstance(node,(ast.If,ast.IfExp,ast.For,ast.AsyncFor,ast.While,ast.Try,ast.Match,ast.BoolOp)) for node in ast.walk(tree)),
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
    cyclic=components(edges)
    local_cyclic=[site for site in local_sites if any(site["source"] in part and site["target"] in part for part in cyclic)]
    return {"scope":"static explicit AST imports; no dynamic import resolution or runtime dependency guarantee",
            "modules":len(modules),"physical_lines":sum(v["physical_lines"] for v in rows.values()),
            "internal_edges":len(edges),"eager_edges":len(eager),"cycles":components(edges),"eager_cycles":components(eager),
            "module_stats":rows,"internal_imports":sorted(edges),"external_imports":sorted(external),
            "eager_imports":sorted(eager),"local_import_sites":local_sites,"cyclic_local_import_sites":local_cyclic,
            "exact_duplicate_body_groups":[v for v in bodies.values() if len(v)>1]}
if __name__=="__main__":print(json.dumps(inspect(),indent=2))
