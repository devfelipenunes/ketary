"""Verify artifact boundaries without executing distributed code."""
from email.parser import BytesParser
from pathlib import PurePosixPath
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
        assert len(names)==len(set(names))
        assert all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts for n in names)
        metadata=[n for n in names if n.endswith(".dist-info/METADATA")]
        assert len(metadata)==1
        meta=BytesParser().parsebytes(z.read(metadata[0]))
        assert meta["Name"]=="ketary" and meta["Version"]=="0.1.0.dev0"
        assert meta["License-Expression"]=="Apache-2.0"
        assert set(meta["Requires-Python"].split(","))=={">=3.12","<3.13"}
        assert set(meta.get_all("Provides-Extra"))=={"dynamic","test"}
        assert any(n.endswith(".dist-info/licenses/LICENSE") for n in names)
        assert "ketary/py.typed" in names and "ketary/__init__.pyi" in names
        assert all(n.startswith("ketary/") or n.split("/")[0].endswith(".dist-info") for n in names)
        assert not any(n.endswith((".so",".dll",".dylib",".pyd")) for n in names)
    with tarfile.open(sdist,"r:gz") as t:
        source=t.getnames()
        assert len(source)==len(set(source))
        assert all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts for n in source)
        assert all(m.isfile() or m.isdir() for m in t.getmembers())
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
