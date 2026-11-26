"""Compare two clean builds from one trusted Git tree; no publication.

Run with the pinned build tooling. Never extract a downloaded archive here.
Content equality and raw byte equality are distinct; report metadata
differences rather than normalize the distributed package after building.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from importlib.metadata import version

def digest(data):
    return hashlib.sha256(data).hexdigest()

def inventory(path):
    data=Path(path).read_bytes()
    if str(path).endswith(".whl"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
            contents={n:digest(z.read(n)) for n in z.namelist()}
            metadata={i.filename:[list(i.date_time),i.external_attr,i.compress_type] for i in z.infolist()}
    elif str(path).endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(data),mode="r:gz") as t:
            members=t.getmembers()
            assert len(members)==len({m.name for m in members})
            assert all(m.isfile() or m.isdir() for m in members)
            contents={m.name:digest(t.extractfile(m).read()) if m.isfile() else None for m in members}
            metadata={m.name:[m.mtime,m.mode,m.uid,m.gid,m.uname,m.gname] for m in members}
    else:
        raise ValueError("expected wheel or sdist")
    return dict(sha256=digest(data),members=contents,metadata=metadata)

def compare(a,b):
    return dict(byte_equal=a["sha256"]==b["sha256"],content_equal=a["members"]==b["members"],
        first_sha256=a["sha256"],second_sha256=b["sha256"],members=len(a["members"]),
        changed_content=sorted(k for k in a["members"].keys()|b["members"].keys() if k not in a["members"] or k not in b["members"] or a["members"][k]!=b["members"][k]),
        changed_metadata=sorted(k for k in a["metadata"].keys()|b["metadata"].keys() if a["metadata"].get(k)!=b["metadata"].get(k)))

def study():
    root=Path(subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip())
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    epoch=subprocess.check_output(["git","show","-s","--format=%ct",commit],cwd=root,text=True).strip()
    archive=subprocess.check_output(["git","archive","--format=tar",commit],cwd=root)
    env=dict(os.environ,SOURCE_DATE_EPOCH=epoch,PYTHONHASHSEED="0",TZ="UTC",LC_ALL="C")
    with tempfile.TemporaryDirectory(prefix="ketary-rebuild-") as tmp:
        outputs=[]
        for slot in ("a","b"):
            source=Path(tmp)/slot
            source.mkdir()
            # Archive created locally by Git from the trusted committed tree.
            with tarfile.open(fileobj=io.BytesIO(archive),mode="r:") as tar:
                tar.extractall(source,filter="data")
            subprocess.run([sys.executable,"-m","build","--no-isolation"],cwd=source,env=env,check=True,stdout=sys.stderr)
            results={}
            for ext in ("*.whl","*.tar.gz"):
                files=list((source/"dist").glob(ext))
                assert len(files)==1
                results[ext]=inventory(files[0])
            outputs.append(results)
        rows={kind:compare(outputs[0][kind],outputs[1][kind]) for kind in outputs[0]}
    return dict(commit=commit,source_date_epoch=epoch,python=sys.version,
        tooling={name:version(name) for name in ("build","setuptools","wheel")},
        scope="two clean source directories from one committed tree, same runner and pinned build tools; no archive rewriting, no installation or publication; byte reproducibility not implied by content equality",results=rows)

if __name__=="__main__":
    report=study()
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    if not all(row["content_equal"] for row in report["results"].values()):
        raise SystemExit("clean build content differs")
