"""Inspect local wheel and sdist archives without extracting or installing."""
import argparse
import hashlib
import json
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path,PurePosixPath

def safe_name(name):
    p=PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and "\\" not in name

def digest(path):
    with open(path,"rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def audit(wheel,sdist):
    wheel,sdist=Path(wheel),Path(sdist)
    with zipfile.ZipFile(wheel) as z:
        names=z.namelist()
        assert len(names)==len(set(names)) and all(safe_name(n) for n in names)
        assert z.testzip() is None
        assert "ketary/py.typed" in names and "ketary/__init__.pyi" in names
        assert not any(n.startswith(("research/","tests/","tests_dynamic/")) for n in names)
        metadata=[n for n in names if n.endswith(".dist-info/METADATA")]
        assert len(metadata)==1
        msg=BytesParser().parsebytes(z.read(metadata[0]))
        assert msg["Name"]=="ketary" and msg["Version"]=="0.1.0.dev0"
        assert msg["Requires-Python"] in (">=3.12,<3.13","<3.13,>=3.12")
        assert any(n.endswith(".dist-info/licenses/LICENSE") for n in names)
        assert any(n.endswith(".dist-info/RECORD") for n in names)
        wheel_count=len(names)
    with tarfile.open(sdist,"r:gz") as t:
        members=t.getmembers()
        assert len(members)==len({m.name for m in members})
        assert all(safe_name(m.name) and (m.isfile() or m.isdir()) for m in members)
        root={PurePosixPath(m.name).parts[0] for m in members}
        assert len(root)==1
        assert any(m.name.endswith("/pyproject.toml") for m in members)
        assert any(m.name.endswith("/LICENSE") for m in members)
        assert not any("/research/" in m.name for m in members)
        sdist_count=len(members)
    return {"wheel":{"sha256":digest(wheel),"members":wheel_count},
            "sdist":{"sha256":digest(sdist),"members":sdist_count},
            "scope":"archive structure and identity only; not reproducible-build or legal review"}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("wheel");p.add_argument("sdist");a=p.parse_args()
    print(json.dumps(audit(a.wheel,a.sdist),indent=2))
