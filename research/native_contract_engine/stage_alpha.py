"""Single-source staging for an isolated, local-only QContract Alpha wheel.

Do not ship the research directory, benchmark executables, ctypes loaders,
or competing historical frontends. Select dependency closure explicitly.
Keep originals in research for regression evidence. This is a provisional
distribution, not an upload or permanent namespace allocation.
"""
import ast,hashlib,json,pathlib,re,sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
LAB=ROOT/"research"/"native_contract_engine"
# Audited dependency closure, not an automatic recursive import sweep.
MODULES=(
    "native9","engine","sparse","round3","contract_forms11","consolidated12",
    "contracts15","monomial16","semantics25","independent20","structures21",
    "contracts18","noise17","facade17","router27","weighted27","weighted25",
    "dag22","expectation23","certificate23","spatial_evidence27","state29",
    "spatial26","unified24","prepared23","planner19","cuts21","logical14",
    "subspace10","candidate28","qualified30","qualified31",
)
# Extract only needed runtime declarations from legacy research modules
# that otherwise import benchmark/ctypes scaffolding. Fail if a selected
# declaration disappears. All mathematical bodies are unchanged.
SELECT={
    "engine":({"dataclasses","hashlib","json"},{"SCOPE","digest","valid_pauli","Obligation","Witness","Report","_add","difference","product_witness"}),
    "sparse":({"dataclasses"},{"Propagation","BudgetExceeded"}),
    "round3":({"qiskit.circuit.library"},{"CLASSES","CODES"}),
    "contracts18":({"dataclasses","fractions","math","facade17","consolidated12","native9","sparse","engine"},{"SumReport","admit_sum","exact_sum"}),
    "facade17":({"contract_forms11"},{"signed"}),
}

def canonical_text(path):
    # Hash repository text in canonical LF form, independent of checkout OS.
    return path.read_text(encoding="utf-8").encode("utf-8")

def extract(src,module):
    if module not in SELECT:return src
    imports,names=SELECT[module];found=set();parts=[];lines=src.splitlines(keepends=True)
    for node in ast.parse(src).body:
        include=False
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):include=True
        elif isinstance(node,ast.Import):include=all(a.name in imports for a in node.names)
        elif isinstance(node,ast.ImportFrom):include=node.module in imports
        elif isinstance(node,(ast.FunctionDef,ast.ClassDef)):include=node.name in names;found.update([node.name] if include else [])
        elif isinstance(node,ast.Assign):
            actual={x.id for x in node.targets if isinstance(x,ast.Name)}
            include=bool(actual&names);found.update(actual&names)
        if include:
            start=min([node.lineno]+[d.lineno for d in getattr(node,"decorator_list",[])])
            parts.append("".join(lines[start-1:node.end_lineno]))
    if found!=names:raise ValueError((module,names-found))
    return "\n\n".join(parts)+"\n"

def rewrite(src,module):
    # All local imports become relative, including deferred imports.
    # No sys.path changes, no top-level research modules shipped.
    src=re.sub(r"(?m)^(\s*)from ([A-Za-z_]\w*) import ",lambda m:m[1]+"from "+("." if m[2] in MODULES else "")+m[2]+" import ",src)
    src=src.replace("import ketary_native_research as rn","import qcontract_native_alpha as rn")
    tree=ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            if node.level==1 and node.module not in MODULES:raise ValueError((module,node.module))
            if node.level==0 and node.module and node.module.split(".")[0] in {"benchmark","test_engine","common5","ctypes"}:raise ValueError((module,node.module))
        if isinstance(node,ast.Import):
            if any(a.name.split(".")[0] in set(MODULES)|{"benchmark","test_engine","common5","ctypes"} for a in node.names):raise ValueError((module,node.names))
    return src

def stage(dest):
    dest=pathlib.Path(dest).resolve()
    if dest.exists():raise ValueError("stage directory must not exist")
    pkg=dest/"src"/"qcontract";private=pkg/"_core";private.mkdir(parents=True)
    (private/"__init__.py").write_bytes(b'"""Private generated runtime; not a supported import path."""\n')
    manifest={}
    for name in MODULES:
        p=LAB/(name+".py");raw=canonical_text(p);src=rewrite(extract(raw.decode("utf-8"),name),name)
        (private/(name+".py")).write_bytes(src.encode("utf-8"))
        manifest[name]={"source_sha256":hashlib.sha256(raw).hexdigest(),"runtime_sha256":hashlib.sha256(src.encode()).hexdigest()}
    api=canonical_text(LAB/"alpha"/"api.py");(pkg/"__init__.py").write_bytes(api)
    stub=canonical_text(LAB/"alpha"/"api.pyi");(pkg/"__init__.pyi").write_bytes(stub)
    (pkg/"py.typed").write_bytes(b"")
    manifest["public_api"]={"source_sha256":hashlib.sha256(api).hexdigest(),"stub_sha256":hashlib.sha256(stub).hexdigest()}
    (pkg/"runtime-manifest.json").write_bytes(json.dumps(manifest,sort_keys=True,indent=2).encode("utf-8"))
    (dest/"LICENSE").write_bytes(canonical_text(ROOT/"LICENSE"))
    (dest/"README.md").write_bytes(canonical_text(ROOT/"docs"/"qcontract-alpha-guide.md"))
    (dest/"pyproject.toml").write_text("""[build-system]
requires = ["setuptools==80.9.0"]
build-backend = "setuptools.build_meta"

[project]
name = "qcontract-alpha-local"
version = "0.1.0a3"
description = "Local experimental QContract verification candidate (not published)"
readme = "README.md"
requires-python = ">=3.12,<3.13"
license = "Apache-2.0"
license-files = ["LICENSE"]
dependencies = ["qiskit==2.6.2", "numpy>=1.26,<3", "qcontract-native-alpha-local==0.1.0"]

[tool.setuptools.packages.find]
where = ["src"]
include = ["qcontract*"]
namespaces = false

[tool.setuptools.package-data]
qcontract = ["runtime-manifest.json", "*.pyi", "py.typed"]
""",encoding="utf-8",newline="\n")
    return {"modules":len(MODULES),"manifest":manifest,"distribution":"qcontract-alpha-local","import":"qcontract","scope":"local candidate only"}

if __name__=="__main__":print(json.dumps(stage(sys.argv[1]),indent=2))
