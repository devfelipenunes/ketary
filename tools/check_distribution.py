"""Verify artifact boundaries without executing distributed code."""
import hashlib
import json
from pathlib import Path
import tarfile
import zipfile

def manifest(root=Path("dist")):
    wheels=list(root.glob("*.whl"))
    sdists=list(root.glob("*.tar.gz"))
    if len(wheels)!=1 or len(sdists)!=1:
        raise ValueError("expected one wheel and one sdist")
    wheel=wheels[0]; sdist=sdists[0]
    with zipfile.ZipFile(wheel) as z:
        names=z.namelist()
        assert any(n.endswith(".dist-info/licenses/LICENSE") for n in names)
        assert "ketary/py.typed" in names and "ketary/__init__.pyi" in names
        assert all(n.startswith("ketary/") or n.split("/")[0].endswith(".dist-info") for n in names)
        assert not any(n.endswith((".so",".dll",".dylib",".pyd")) for n in names)
    with tarfile.open(sdist,"r:gz") as t:
        source=t.getnames()
        assert any(n.endswith("/LICENSE") for n in source)
        assert any(n.endswith("/src/ketary/py.typed") for n in source)
        assert all(not n.endswith((".so",".dll",".dylib",".pyd")) for n in source)
    return {"artifacts":[{"name":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"members":members}
        for p,members in [(wheel,names),(sdist,source)]],
        "scope":"artifact membership only; not a legal opinion or signature"}

if __name__=="__main__":
    data=manifest()
    Path("distribution-manifest.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data,indent=2))
