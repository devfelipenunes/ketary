"""The backend decision must not expand the installed SDK boundary."""
import ast
from pathlib import Path
import tomllib

ROOT=Path(__file__).resolve().parents[1]

def test_native_research_not_an_installed_dependency():
    project=tomllib.loads((ROOT/"pyproject.toml").read_text())
    assert set(project["project"]["dependencies"])=={"qiskit==2.6.2","numpy>=1.26,<3"}
    assert set(project["project"]["optional-dependencies"])=={"dynamic","test"}
    assert project["tool"]["setuptools"]["packages"]["find"]["where"]==["src"]

def test_no_research_native_bridge_import_in_runtime():
    forbidden={"research","_ketary_capi_probe","quest_extended_probe","quest_probe","prepared_native","combined_native_benchmark"}
    for path in (ROOT/"src"/"ketary").rglob("*.py"):
        tree=ast.parse(path.read_text(),filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                assert not ({x.name.split(".")[0] for x in node.names}&forbidden),path
            elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
                assert node.module.split(".")[0] not in forbidden,path
    assert not any(p.suffix in {".so",".dll",".dylib",".pyd"} for p in (ROOT/"src"/"ketary").rglob("*"))

def test_research_abi_pins_and_gate_decision_documented():
    text=(ROOT/"docs"/"native-backend-decision.md").read_text()
    assert "NO-GO" in text and "9d7618d7263e3bfba433b88cf1eac0647f08fa0a" in text
    for path in (".github/workflows/native-abi.yml",".github/workflows/extended-native.yml"):
        assert "9d7618d7263e3bfba433b88cf1eac0647f08fa0a" in (ROOT/path).read_text()
