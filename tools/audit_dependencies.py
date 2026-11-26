"""Inventory installed dependencies and declared license metadata.

Run in a fresh validation venv, before installing auditing tools.
Metadata is evidence for manual review, not a legal compatibility opinion.
"""
import importlib.metadata as metadata
import argparse
import hashlib
import json
import platform
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOTS = ("qiskit", "numpy", "pytest", "coverage", "mypy")

def inventory(roots=ROOTS):
    pending = list(roots)
    seen = {}
    while pending:
        name = canonicalize_name(pending.pop())
        if name in seen:
            continue
        dist = metadata.distribution(name)
        m = dist.metadata
        requires = []
        for entry in dist.requires or []:
            req = Requirement(entry)
            if req.marker is None or req.marker.evaluate({"extra": ""}):
                requires.append(str(req))
                pending.append(req.name)
        notices=[]
        for file in dist.files or []:
            parts=str(file).lower().split("/")
            if any(p.endswith(".dist-info") for p in parts) and any(p.startswith(("license","notice","copying","authors")) for p in parts):
                path=dist.locate_file(file)
                if path.is_file():
                    notices.append({"path":str(file),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        seen[name] = {
            "name": m["Name"],
            "version": dist.version,
            "license_expression": m.get("License-Expression"),
            "license": (m.get("License") or "")[:500],
            "license_classifiers": [c for c in m.get_all("Classifier", []) if c.startswith("License ::")],
            "license_files": m.get_all("License-File", []),
            "installed_notice_hashes": sorted(notices,key=lambda x:x["path"]),
            "requires": sorted(requires),
        }
    return {"python": platform.python_version(), "roots": roots,
            "dependencies": [seen[k] for k in sorted(seen)]}

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--scope",choices=["validation","runtime","build","dynamic"],default="validation")
    args=parser.parse_args()
    roots={"validation":ROOTS,"runtime":("qiskit","numpy"),"build":("build","twine","setuptools","wheel"),"dynamic":("qiskit","numpy","qiskit-aer")}[args.scope]
    data = inventory(roots)
    data["scope"]=args.scope
    prefix="" if args.scope=="validation" else args.scope+"-"
    Path(prefix+"license-inventory.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    Path(prefix+"audited-requirements.txt").write_text(
        "".join(f"{d['name']}=={d['version']}\n" for d in data["dependencies"]),
        encoding="utf-8")
    print(json.dumps(data, indent=2))
