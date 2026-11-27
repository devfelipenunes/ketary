"""Offline recheck of cross-platform pure-Python wheel normalization.

Supply existing Python wheel files from the same commit/build version.
Verify original RECORD and require identical normalized archives, without
changing the inputs. No native build, registry, or execution of wheel code.
"""
import base64,csv,hashlib,io,json,pathlib,sys,tempfile,zipfile
from qualify import canonical_python_zip

def sha(data):return hashlib.sha256(data).hexdigest()
def validate(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        assert len(names)==len(set(names)) and z.testzip() is None
        assert all(not n.startswith("/") and ".." not in pathlib.PurePosixPath(n).parts for n in names)
        record,=tuple(n for n in names if n.endswith(".dist-info/RECORD"))
        rows=list(csv.reader(io.StringIO(z.read(record).decode("utf-8"))))
        assert len(rows)==len(names) and {r[0] for r in rows}==set(names)
        for n,h,size in rows:
            if n==record:assert h==size==""
            else:
                data=z.read(n)
                want=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
                assert h=="sha256="+want and int(size)==len(data)
        assert not any(n.endswith((".so",".pyd",".dll",".dylib")) for n in names)
        return len(names)
def verify(paths):
    if len(paths)<2:raise ValueError("at least two platform Python wheels")
    reports=[]
    with tempfile.TemporaryDirectory() as tmp:
        for i,src in enumerate(map(pathlib.Path,paths)):
            data=src.read_bytes();p=pathlib.Path(tmp)/str(i)/src.name;p.parent.mkdir()
            p.write_bytes(data);count=validate(p)
            canonical_python_zip(p);assert validate(p)==count
            normalized=p.read_bytes()
            canonical_python_zip(p);assert p.read_bytes()==normalized
            assert src.read_bytes()==data
            reports.append({"file":str(src),"original":sha(data),"normalized":sha(normalized),"members":count,"idempotent":True})
    assert len({r["normalized"] for r in reports})==1,"normalized wheels differ"
    return {"wheels":reports,"scope":"offline existing wheel normalization, not cross-host build reproduction"}

if __name__=="__main__":print(json.dumps(verify(sys.argv[1:]),indent=2))
