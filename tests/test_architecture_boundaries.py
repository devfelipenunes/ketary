"""Guard direct dependency boundaries and optional integration isolation."""
import ast
from pathlib import Path
import subprocess
import sys
import ketary as q

def test_native_import_boundary_inventory():
    expected={
        "qiskit":{"_adapter","_checks","_circuit","_classical","_observable","_replay","_result","_transpilation","_verification"},
        "numpy":{"_checks","_execution","_result","_trace","_validation","_verification"},
        "qiskit_aer":{"_classical"},
        "mqt":{"_external"},
    }
    observed={key:set() for key in expected}
    for path in Path(q.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):
                roots=[alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
                roots=[node.module.split(".")[0]]
            else:
                continue
            for root in roots:
                if root in observed:
                    observed[root].add(path.stem)
    assert observed==expected

def test_core_workflow_without_optional_backends():
    script="""
import sys
from importlib.abc import MetaPathFinder
class BlockOptional(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'qiskit_aer','mqt'}:
            raise ImportError('optional backend blocked')
sys.meta_path.insert(0,BlockOptional())
import ketary as q
assert 'qiskit' not in sys.modules
XX=q.X(0)@q.X(1)
assert 'qiskit' not in sys.modules
c=q.bell()
r=c.run()
c.contract(expectations={XX:1}).verify(r).require()
assert not any(name.split('.')[0] in {'qiskit_aer','mqt'} for name in sys.modules)
"""
    subprocess.run([sys.executable,"-c",script],check=True)


def test_eager_internal_import_graph_is_acyclic():
    """Function-local imports are excluded; they can still form runtime cycles."""
    root=Path(q.__file__).parent
    modules={path.stem for path in root.glob("*.py")}
    graph={module:set() for module in modules}
    class EagerImports(ast.NodeVisitor):
        def __init__(self,module):
            self.module=module
        def visit_FunctionDef(self,node):
            pass
        visit_AsyncFunctionDef=visit_FunctionDef
        def visit_ImportFrom(self,node):
            if node.level==1:
                names=[node.module.split(".")[0]] if node.module else [a.name for a in node.names]
            elif node.level==0 and node.module and node.module.startswith("ketary."):
                names=[node.module.split(".")[1]]
            elif node.level==0 and node.module=="ketary":
                names=["__init__"]
            else:
                names=[]
            graph[self.module].update(name for name in names if name in modules)
        def visit_Import(self,node):
            for alias in node.names:
                if alias.name=="ketary":
                    graph[self.module].add("__init__")
                elif alias.name.startswith("ketary."):
                    name=alias.name.split(".")[1]
                    if name in modules:
                        graph[self.module].add(name)
    for path in root.glob("*.py"):
        EagerImports(path.stem).visit(ast.parse(path.read_text()))
    visited=set()
    def visit(node,ancestors):
        assert node not in ancestors, "eager import cycle: "+" -> ".join((*ancestors,node))
        if node in visited:
            return
        for dep in sorted(graph[node]):
            visit(dep,(*ancestors,node))
        visited.add(node)
    for module in sorted(graph):
        visit(module,())
    assert not graph["_validation"]
    assert not graph["_gate_specs"]
    assert not graph["_execution"]-{"_adapter","_result","_validation"}
    assert "__init__" not in set().union(*(deps for module,deps in graph.items() if module!="__init__"))
