"""Verify wheel contents, RECORD hashes and project license; not a legal audit."""
import base64,csv,hashlib,io,json,pathlib,sys,zipfile
p=pathlib.Path(sys.argv[1]);ws=list(p.glob("*.whl"));assert len(ws)==1
w=ws[0]
with zipfile.ZipFile(w) as z:
    assert z.testzip() is None
    names=z.namelist();assert len(set(names))==len(names)
    assert all(not n.startswith("/") and ".." not in pathlib.PurePosixPath(n).parts for n in names)
    rec=next(n for n in names if n.endswith(".dist-info/RECORD"))
    rows=list(csv.reader(io.StringIO(z.read(rec).decode())))
    assert len(rows)==len(names) and {r[0] for r in rows}==set(names)
    for n,h,s in rows:
        if n==rec:assert not h and not s;continue
        b=z.read(n);assert h=="sha256="+base64.urlsafe_b64encode(hashlib.sha256(b).digest()).decode().rstrip("=") and int(s)==len(b)
    licenses=[n for n in names if n.endswith("/LICENSE") and ".dist-info/" in n]
    assert licenses,"project license missing"
    print(json.dumps({"wheel":w.name,"record_entries":len(rows),"project_license_paths":licenses,"sha256":hashlib.sha256(w.read_bytes()).hexdigest(),"scope":"integrity and own project license only; third-party notice/legal approval pending"},indent=2))
