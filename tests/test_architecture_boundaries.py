"""Guard direct dependency boundaries and optional integration isolation."""
import ast
from pathlib import Path
import subprocess
import sys
import ketary as q

def test_native_import_boundary_inventory():
    expected={
        "qiskit":{"_adapter","_checks","_circuit","_classical","_observable","_replay","_result","_transpilation","_verification"},
        "numpy":{"_checks","_circuit","_result","_trace","_validation","_verification"},
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
