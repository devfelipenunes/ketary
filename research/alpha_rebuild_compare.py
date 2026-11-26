"""Compare two clean builds from one trusted Git tree; no publication.

Run with the pinned build tooling. Never extract a downloaded archive here.
Content equality and raw byte equality are distinct; report metadata
differences rather than normalize the distributed package after building.
"""
import gzip
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

def deterministic_tar(base_name, base_dir, epoch):
    """Research-only archive creation from setuptools' original release tree."""
    path=Path(str(base_name)+".tar.gz")
    path.parent.mkdir(parents=True,exist_ok=True)
    root=Path(base_dir)
    if not root.is_dir() or root.is_absolute() or len(root.parts)!=1:
        raise ValueError("expected a local setuptools release directory")
    def fixed(info):
        if not (info.isfile() or info.isdir()):
            raise ValueError("non-regular release member")
        info.mtime=epoch
        info.uid=info.gid=0
        info.uname=info.gname=""
        info.pax_headers={}
        return info
    with path.open("wb") as stream:
        with gzip.GzipFile(filename="",mode="wb",fileobj=stream,mtime=epoch) as gz:
            with tarfile.open(fileobj=gz,mode="w|",format=tarfile.PAX_FORMAT) as archive:
                archive.add(root,arcname=root.name,filter=fixed)
    return str(path)

def build_candidate_sdist(destination):
    # Never patch the installed runtime, production backend configuration, or
    # existing archive. Limit this experimental hook to the pinned build tool.
    from setuptools import build_meta
    from setuptools.command.sdist import sdist
    from unittest.mock import patch
    if version("setuptools")!="84.2.1":
        raise RuntimeError("diagnostic requires pinned setuptools 84.2.1")
    epoch=int(os.environ["SOURCE_DATE_EPOCH"])
    if not 0<=epoch<2**32:raise ValueError("invalid gzip epoch")
    original=sdist.make_archive
    calls=[]
    def make_archive(self,base_name,format,root_dir=None,base_dir=None,owner=None,group=None):
        if format!="gztar" or root_dir is not None or owner is not None or group is not None:
            raise RuntimeError("unsupported experimental archive parameters")
        calls.append(format)
        return deterministic_tar(base_name,base_dir,epoch)
    with patch.object(sdist,"make_archive",make_archive):
        name=build_meta.build_sdist(str(Path(destination).resolve()))
    if calls!=["gztar"]:raise RuntimeError("expected exactly one candidate archive creation")
    return name

def study():
    root=Path(subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip())
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    epoch=subprocess.check_output(["git","show","-s","--format=%ct",commit],cwd=root,text=True).strip()
    archive=subprocess.check_output(["git","archive","--format=tar",commit],cwd=root)
    env=dict(os.environ,SOURCE_DATE_EPOCH=epoch,PYTHONHASHSEED="0",TZ="UTC",LC_ALL="C")
    with tempfile.TemporaryDirectory(prefix="ketary-rebuild-") as tmp:
        outputs=[]
        candidates=[]
        candidate_wheels=[]
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
            candidate_dir=source/"candidate-dist"
            candidate_dir.mkdir()
            subprocess.run([sys.executable,str(root/"research/alpha_rebuild_compare.py"),"--candidate-sdist",str(candidate_dir)],cwd=source,env=env,check=True,stdout=sys.stderr)
            files=list(candidate_dir.glob("*.tar.gz"))
            assert len(files)==1
            candidates.append(inventory(files[0]))
            subprocess.run([sys.executable,"-m","pip","wheel","--no-deps","--no-build-isolation","--wheel-dir",str(candidate_dir),str(files[0])],cwd=source,env=env,check=True,stdout=sys.stderr)
            wheels=list(candidate_dir.glob("*.whl"))
            assert len(wheels)==1
            candidate_wheels.append(inventory(wheels[0]))
        rows={kind:compare(outputs[0][kind],outputs[1][kind]) for kind in outputs[0]}
        candidate_rows=dict(sdist=compare(*candidates),wheel_from_sdist=compare(*candidate_wheels),stock_sdist_content=compare(outputs[0]["*.tar.gz"],candidates[0]),stock_wheel_content=compare(outputs[0]["*.whl"],candidate_wheels[0]))
    return dict(commit=commit,source_date_epoch=epoch,python=sys.version,
        tooling={name:version(name) for name in ("build","setuptools","wheel")},
        scope="two clean source directories from one committed tree, same runner and pinned build tools; no archive rewriting, no installation or publication; byte reproducibility not implied by content equality",results=rows,candidate=candidate_rows)

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--candidate-sdist":
        print(build_candidate_sdist(sys.argv[2]));raise SystemExit(0)
    report=study()
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    if not all(row["content_equal"] for row in report["results"].values()):
        raise SystemExit("clean build content differs")
    if not all(row["content_equal"] for row in report["candidate"].values()):
        raise SystemExit("candidate changed distribution content")
    if not all(report["candidate"][k]["byte_equal"] for k in ("sdist","wheel_from_sdist")):
        raise SystemExit("candidate byte reproducibility not demonstrated")
