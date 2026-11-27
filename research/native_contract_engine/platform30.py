"""Build twice in independent target directories, audit, install, smoke test.
Same-host repeatability diagnostic only; no cross-host equality claim."""
import hashlib,json,os,pathlib,platform,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
lab=root/"research"/"native_contract_engine"
crate=lab/"pyo3"
out=root/"qualification30"
out.mkdir(exist_ok=True)
def run(args,**kw):
    return subprocess.run(args,check=True,**kw)
def build(i):
    dest=out/("wheel"+str(i));dest.mkdir(exist_ok=True)
    env=dict(os.environ,CARGO_TARGET_DIR=str(out/("target"+str(i))),CARGO_INCREMENTAL="0",SOURCE_DATE_EPOCH="1700000000")
    run([sys.executable,"-m","maturin","build","--release","--locked","--interpreter",sys.executable,"--compatibility","off","--out",str(dest)],cwd=crate,env=env)
    wheels=list(dest.glob("*.whl"));assert len(wheels)==1
    with (out/("wheel-audit-"+str(i)+".json")).open("w",encoding="utf-8") as f:
        run([sys.executable,str(lab/"wheel_audit10.py"),str(dest)],stdout=f)
    return wheels[0]
def main():
    a,b=build(1),build(2);ha=hashlib.sha256(a.read_bytes()).hexdigest();hb=hashlib.sha256(b.read_bytes()).hexdigest()
    run([sys.executable,"-m","pip","install","--no-deps",str(a)])
    run([sys.executable,"-m","pip","check"])
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    with (out/"cargo.json").open("w",encoding="utf-8") as f:run(["cargo","metadata","--locked","--format-version","1"],cwd=crate,stdout=f)
    with (out/"sbom.cdx.json").open("w",encoding="utf-8") as f:
        run([sys.executable,str(lab/"sbom30.py"),str(out/"cargo.json"),str(crate/"Cargo.lock"),str(a),commit],stdout=f)
    for name,script,suite in (("ffi","front_master29.py","ffi"),("integrated","front_master30.py","integrated"),("simd","front_master25.py","simd")):
        with (out/(name+".json")).open("w",encoding="utf-8") as f:run([sys.executable,str(lab/script),suite],stdout=f)
    bom=json.loads((out/"sbom.cdx.json").read_text(encoding="utf-8"))
    result={"commit":commit,"platform":platform.platform(),"machine":platform.machine(),"python":sys.version,
            "rustc":subprocess.check_output(["rustc","--version","--verbose"],text=True),
            "wheel":a.name,"sha256_a":ha,"sha256_b":hb,"same_host_identical":ha==hb,
            "component_count":len(bom["components"]),"scope":"independent target dirs, same host; no cross-host reproducibility or legal clearance"}
    (out/"platform.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
if __name__=="__main__":main()
