"""Audit R30 platform artifacts and collect local dependency notice files.
Metadata and collected license text inventory are not legal clearance.
"""
import hashlib,importlib.metadata as md,json,pathlib,struct,sys,zipfile
from packaging.utils import canonicalize_name

def sha(b):return hashlib.sha256(b).hexdigest()
def pe_stamp(data):
    if data[:2]!=b"MZ" or len(data)<64:return None
    p=struct.unpack_from("<I",data,0x3c)[0]
    if p+12>len(data) or data[p:p+4]!=b"PE\0\0":return None
    return struct.unpack_from("<I",data,p+8)[0]
def compare(a,b):
    with zipfile.ZipFile(a) as x,zipfile.ZipFile(b) as y:
        assert set(x.namelist())==set(y.namelist())
        rows=[]
        for n in sorted(x.namelist()):
            u,v=x.read(n),y.read(n)
            if u!=v:
                rows.append({"entry":n,"size_a":len(u),"size_b":len(v),
                             "sha_a":sha(u),"sha_b":sha(v),
                             "different_overlap_bytes":sum(p!=q for p,q in zip(u,v)),
                             "pe_stamp_a":pe_stamp(u),"pe_stamp_b":pe_stamp(v)})
        return rows

def notices(cargo,out):
    rows=[];out.mkdir(exist_ok=True)
    def record(scope,name,version,files,license_meta):
        saved=[]
        for f in files:
            if not f.is_file():continue
            data=f.read_bytes()
            if len(data)>2_000_000:raise ValueError("notice size")
            h=sha(data);dest=out/(h+".txt")
            dest.write_bytes(data)
            saved.append({"name":f.name,"sha256":h,"bytes":len(data)})
        rows.append({"scope":scope,"name":name,"version":version,"license_metadata":license_meta or "UNKNOWN","files":saved})
    for p in cargo["packages"]:
        root=pathlib.Path(p["manifest_path"]).parent
        candidates=[f for f in root.iterdir() if f.is_file() and f.name.upper().startswith(("LICENSE","LICENCE","COPYING","NOTICE"))]
        if p.get("license_file"):
            f=root/p["license_file"]
            if f.is_file() and f not in candidates:candidates.append(f)
        record("cargo",p["name"],p["version"],candidates,p.get("license"))
    for d in md.distributions():
        name=d.metadata["Name"]
        if not name:continue
        candidates=[]
        for f in d.files or ():
            path=pathlib.PurePosixPath(str(f))
            if any(p.endswith(".dist-info") for p in path.parts) and (path.name.upper().startswith(("LICENSE","LICENCE","COPYING","NOTICE")) or "licenses" in path.parts):
                candidates.append(pathlib.Path(d.locate_file(f)))
        record("python",canonicalize_name(name),d.version,candidates,d.metadata.get("License-Expression") or d.metadata.get("License"))
    rows.sort(key=lambda r:(r["scope"],r["name"],r["version"]))
    return {"components":rows,"missing_notice_files":[[r["scope"],r["name"],r["version"]] for r in rows if not r["files"]],"scope":"local component notice collection, missing text requires review; not legal clearance"}

if __name__=="__main__":
    p=pathlib.Path(sys.argv[1])
    a,=list((p/"wheel1").glob("*.whl"));b,=list((p/"wheel2").glob("*.whl"))
    result={"wheel_a":sha(a.read_bytes()),"wheel_b":sha(b.read_bytes()),"different_entries":compare(a,b)}
    (p/"wheel-diff.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    cargo=json.loads((p/"cargo.json").read_text(encoding="utf-8"))
    inventory=notices(cargo,p/"notice-texts")
    (p/"notices.json").write_text(json.dumps(inventory,indent=2,ensure_ascii=True),encoding="utf-8")
