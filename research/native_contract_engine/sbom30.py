"""Research candidate component inventory in CycloneDX 1.5 format.

Cargo resolved graph and Python installed distributions are separate scopes.
License metadata is retained verbatim for review, not legal approval.
No vulnerability-free or exact wheel linkage claim.
"""
import hashlib,importlib.metadata as md,json,pathlib,sys,tomllib
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

def inventory(cargo,lock,wheel,commit):
    packages=cargo["packages"];locked={(p["name"],p["version"]):p for p in lock["package"]}
    components=[];edges=[];ids={}
    for p in packages:
        key=p["id"];ref="cargo:"+key;ids[key]=ref
        c={"type":"library","name":p["name"],"version":p["version"],"bom-ref":ref,
           "properties":[{"name":"ketary:scope","value":"cargo-resolved-build-graph"},
                         {"name":"ketary:license-metadata","value":p.get("license") or "UNKNOWN"}]}
        if p.get("source","") and p["source"].startswith("registry+"):
            c["purl"]="pkg:cargo/"+p["name"]+"@"+p["version"]
            h=locked[(p["name"],p["version"])]["checksum"];assert len(h)==64
            c["hashes"]=[{"alg":"SHA-256","content":h}]
        components.append(c)
    for node in cargo["resolve"]["nodes"]:
        edges.append({"ref":ids[node["id"]],"dependsOn":sorted(ids[d] for d in node["dependencies"])})
    ds={canonicalize_name(d.metadata["Name"]):d for d in md.distributions() if d.metadata["Name"]}
    for name,d in sorted(ds.items()):
        ref="python:"+name+"@"+d.version
        c={"type":"library","name":name,"version":d.version,"bom-ref":ref,"purl":"pkg:pypi/"+name+"@"+d.version,
           "properties":[{"name":"ketary:scope","value":"installed-test-environment"},
                         {"name":"ketary:license-metadata","value":d.metadata.get("License-Expression") or d.metadata.get("License") or "UNKNOWN"}]}
        components.append(c)
        deps=set()
        for spec in d.requires or ():
            r=Requirement(spec);k=canonicalize_name(r.name)
            if k in ds and (r.marker is None or r.marker.evaluate({"extra":""})):deps.add("python:"+k+"@"+ds[k].version)
        edges.append({"ref":ref,"dependsOn":sorted(deps)})
    w=pathlib.Path(wheel);ref="candidate-wheel:"+w.name
    root={"type":"file","name":w.name,"bom-ref":ref,"hashes":[{"alg":"SHA-256","content":hashlib.sha256(w.read_bytes()).hexdigest()}],
          "properties":[{"name":"ketary:commit","value":commit},{"name":"ketary:scope","value":"research-wheel; environment graph is not a binary linkage map"}]}
    components.sort(key=lambda c:c["bom-ref"]);edges.sort(key=lambda c:c["ref"])
    refs={c["bom-ref"] for c in components}
    assert len(refs)==len(components) and all(e["ref"] in refs and set(e["dependsOn"])<=refs for e in edges)
    return {"bomFormat":"CycloneDX","specVersion":"1.5","version":1,"metadata":{"component":root},"components":components,"dependencies":edges}

if __name__=="__main__":
    cargo=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    lock=tomllib.loads(pathlib.Path(sys.argv[2]).read_text())
    bom=inventory(cargo,lock,sys.argv[3],sys.argv[4])
    print(json.dumps(bom,indent=2,ensure_ascii=True))
