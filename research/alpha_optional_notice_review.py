"""Read only pinned public wheel ZIP members; never install or execute them."""
import argparse
import email
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

EXPECTED={
    "antlr4_python3_runtime-4.13.2-py3-none-any.whl":"fe3835eb8d33daece0e799090eda89719dbccee7aa39ef94eed3818cafa5a7e8",
    "nanobind_backend-1.0.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl":"6aa9864050cc5fd1ff59d1f9b79740efa278515eed27af848efae07125c029b8",
}

def inspect(path,expected):
    raw=path.read_bytes()
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected:raise ValueError("wheel hash mismatch")
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:raise ValueError("invalid ZIP")
        meta=[n for n in names if n.endswith(".dist-info/METADATA")]
        if len(meta)!=1:raise ValueError("expected one metadata member")
        m=email.message_from_bytes(z.read(meta[0]))
        files=[]
        for n in names:
            if n.endswith("/"):continue
            parts=PurePosixPath(n).parts
            if any(p.lower().startswith(("license","licence","notice","copying","copyright","authors")) for p in parts):
                files.append({"path":n,"sha256":hashlib.sha256(z.read(n)).hexdigest()})
        return dict(filename=path.name,sha256=actual,name=m["Name"],version=m["Version"],
                    license=m.get("License"),license_expression=m.get("License-Expression"),
                    license_files=m.get_all("License-File",[]),classifiers=m.get_all("Classifier",[]),
                    candidate_notice_files=files,members=names)

def review(directory):
    return {"scope":"pinned public wheel filename/hash/member evidence only; candidate names not a legal opinion; no installation, execution, binary provenance or redistribution approval",
            "wheels":[inspect(directory/name,sha) for name,sha in EXPECTED.items()]}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("directory",type=Path);a=p.parse_args()
    print(json.dumps(review(a.directory),indent=2))
