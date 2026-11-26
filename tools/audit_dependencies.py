"""Inventory installed dependencies and declared license metadata.

Run in a fresh validation venv, before installing auditing tools.
Metadata is evidence for manual review, not a legal compatibility opinion.
"""
import importlib.metadata as metadata
import json
import platform
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOTS = ("qiskit", "numpy", "pytest", "coverage", "mypy")

def inventory():
    pending = list(ROOTS)
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
        seen[name] = {
            "name": m["Name"],
            "version": dist.version,
            "license_expression": m.get("License-Expression"),
            "license": (m.get("License") or "")[:500],
            "license_classifiers": [c for c in m.get_all("Classifier", []) if c.startswith("License ::")],
            "license_files": m.get_all("License-File", []),
            "requires": sorted(requires),
        }
    return {"python": platform.python_version(), "roots": ROOTS,
            "dependencies": [seen[k] for k in sorted(seen)]}

if __name__ == "__main__":
    data = inventory()
    Path("license-inventory.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    Path("audited-requirements.txt").write_text(
        "".join(f"{d['name']}=={d['version']}\n" for d in data["dependencies"]),
        encoding="utf-8")
    print(json.dumps(data, indent=2))
