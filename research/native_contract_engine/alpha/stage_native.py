"""Stage an Alpha-only native crate without touching historical lab names.

The source bodies are copied byte-for-byte after canonical LF conversion
and a constrained namespace substitution. No dependency versions change.
"""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
SOURCE=ROOT/"research"/"native_contract_engine"/"pyo3"
FILES=("Cargo.toml","Cargo.lock","pyproject.toml","LICENSE","src/core.rs","src/lib.rs","src/monomial.rs","src/simd25.rs","src/tableau22.rs")
def stage(dest):
    dest=pathlib.Path(dest).resolve();dest.mkdir(exist_ok=False)
    manifest={}
    for name in FILES:
        raw=(SOURCE/name).read_text(encoding="utf-8")
        text=raw if name=="LICENSE" else raw.replace("ketary-native-research","qcontract-native-alpha-local").replace("ketary_native_research","qcontract_native_alpha")
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode("utf-8"))
        manifest[name]={"source_sha256":hashlib.sha256(raw.encode()).hexdigest(),"staged_sha256":hashlib.sha256(text.encode()).hexdigest()}
    return manifest
if __name__=="__main__":print(json.dumps(stage(sys.argv[1]),indent=2,sort_keys=True))
