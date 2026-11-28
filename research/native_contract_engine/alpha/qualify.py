"""Build and test the isolated local Alpha candidate on one CI platform.

Uses a fresh venv with no legacy distribution and no editable installs.
Artifacts include the native and Python wheels, exact commit, wheel
hashes, installed dependency inventory and smoke results. No publication.
"""
import base64,csv,hashlib,io,json,os,pathlib,platform,subprocess,sys,venv,zipfile

ROOT=pathlib.Path(__file__).resolve().parents[3]
LAB=ROOT/"research"/"native_contract_engine"
OUT=ROOT/"qcontract-qualification"
def run(args,**kw):
    return subprocess.run([str(a) for a in args],check=True,**kw)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def source_sha(p):
    return hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
def canonical_python_zip(w):
    # Pure Python wheel only: normalize the metadata line endings that
    # setuptools writes in platform text mode. Recompute RECORD explicitly.
    # No executable/source/manifest bytes or native wheel are changed.
    tmp=w.with_suffix(".tmp")
    with zipfile.ZipFile(w) as src:
        names=src.namelist()
        assert len(names)==len(set(names)) and not any(n.endswith((".jws",".p7s")) for n in names)
        data={n:src.read(n) for n in names}
    metadata,=tuple(n for n in names if n.endswith(".dist-info/METADATA"))
    record,=tuple(n for n in names if n.endswith(".dist-info/RECORD"))
    data[metadata]=data[metadata].replace(b"\r\n",b"\n")
    rows=io.StringIO(newline="")
    writer=csv.writer(rows,lineterminator="\n")
    for n in sorted(set(names)-{record}):
        value=data[n]
        digest=base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b"=").decode("ascii")
        writer.writerow((n,"sha256="+digest,len(value)))
    writer.writerow((record,"",""))
    data[record]=rows.getvalue().encode("utf-8")
    with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_STORED) as dst:
        for n in sorted(names,key=lambda n:(".dist-info/" in n,n.endswith("/RECORD"),n)):
            info=zipfile.ZipInfo(n,date_time=(2023,11,14,22,13,20))
            info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_STORED
            dst.writestr(info,data[n])
    with zipfile.ZipFile(w) as src,zipfile.ZipFile(tmp) as dst:
        assert set(src.namelist())==set(dst.namelist())
        assert all(src.read(n)==dst.read(n) for n in names if n not in (metadata,record))
        assert src.read(metadata).replace(b"\r\n",b"\n")==dst.read(metadata)
    tmp.replace(w)

def audit_python(w):
    with zipfile.ZipFile(w) as z:
        names=z.namelist()
        assert z.testzip() is None and len(names)==len(set(names))
        assert not any(n.startswith("/") or ".." in pathlib.PurePosixPath(n).parts for n in names)
        assert all(n.startswith("qcontract/") or ".dist-info/" in n for n in names)
        assert not any("/benchmark" in n or "/front_" in n or "/test_" in n for n in names)
        assert any(n.endswith("/licenses/LICENSE") for n in names)
        manifest=json.loads(z.read("qcontract/runtime-manifest.json"))
        for name,row in manifest.items():
            path="qcontract/__init__.py" if name=="public_api" else "qcontract/_core/"+name+".py"
            source=LAB/"alpha"/"api.py" if name=="public_api" else LAB/(name+".py")
            assert source_sha(source)==row["source_sha256"]
            want=row.get("runtime_sha256",row["source_sha256"])
            assert hashlib.sha256(z.read(path)).hexdigest()==want
        assert "qcontract/py.typed" in names
        assert hashlib.sha256(z.read("qcontract/__init__.pyi")).hexdigest()==manifest["public_api"]["stub_sha256"]==source_sha(LAB/"alpha"/"api.pyi")
        return {"entries":len(names),"runtime_modules":len(manifest)-1,"sha256":sha(w)}
def main():
    OUT.mkdir(exist_ok=False)
    env=dict(os.environ,SOURCE_DATE_EPOCH="1700000000",CARGO_INCREMENTAL="0",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    if os.name=="nt":env["RUSTFLAGS"]="-C link-arg=/Brepro"
    native=OUT/"native";native.mkdir()
    crate=OUT/"native-stage"
    with (OUT/"native-stage.json").open("w",encoding="utf-8") as f:
        run([sys.executable,LAB/"alpha"/"stage_native.py",crate],stdout=f)
    # Linux must pass Maturin's manylinux policy audit; never just rename
    # a native wheel. Use the audited tag and independently check ELF.
    compatibility="manylinux_2_34" if sys.platform=="linux" else "off"
    run([sys.executable,"-m","maturin","build","--release","--locked","--interpreter",sys.executable,"--compatibility",compatibility,"--out",native],cwd=crate,env=env)
    nw,=native.glob("*.whl")
    if sys.platform=="linux":
        assert "manylinux_2_34_x86_64" in nw.name
        with (OUT/"linux-abi.json").open("w",encoding="utf-8") as f:
            run([sys.executable,LAB/"alpha"/"linux_abi.py",nw],stdout=f)
    with (OUT/"native-audit.json").open("w",encoding="utf-8") as f:
        run([sys.executable,LAB/"wheel_audit10.py",native],stdout=f)
    staged=OUT/"staged"
    with (OUT/"stage.json").open("w",encoding="utf-8") as f:
        run([sys.executable,LAB/"stage_alpha.py",staged],stdout=f)
    pywheel=OUT/"python";pywheel.mkdir()
    run([sys.executable,"-m","pip","wheel","--no-deps","--no-build-isolation","--wheel-dir",pywheel,staged],env=env)
    pw,=pywheel.glob("*.whl")
    with (OUT/"python-original-record-audit.json").open("w",encoding="utf-8") as f:
        run([sys.executable,LAB/"wheel_audit10.py",pywheel],stdout=f)
    canonical_python_zip(pw)
    audit=audit_python(pw)
    with (OUT/"runtime-closure.json").open("w",encoding="utf-8") as f:
        run([sys.executable,LAB/"alpha"/"runtime_audit.py",pw],stdout=f)
    with (OUT/"python-record-audit.json").open("w",encoding="utf-8") as f:
        run([sys.executable,LAB/"wheel_audit10.py",pywheel],stdout=f)
    venv_dir=OUT/"venv";venv.EnvBuilder(with_pip=True,system_site_packages=False).create(venv_dir)
    python=venv_dir/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    run([python,"-m","pip","install","-c",ROOT/"constraints/linux-py312.txt",nw,pw],env=env)
    run([python,"-m","pip","check"],env=env)
    with (OUT/"environment.json").open("w",encoding="utf-8") as f:run([python,"-m","pip","list","--format=json"],stdout=f,env=env)
    with (OUT/"smoke.json").open("w",encoding="utf-8") as f:
        run([python,"-I",LAB/"alpha"/"smoke.py"],cwd=OUT,stdout=f,env=env)
    with (OUT/"benchmark-api.json").open("w",encoding="utf-8") as f:
        run([python,"-I",LAB/"alpha"/"benchmark_api.py"],cwd=OUT,stdout=f,env=env)
    with (OUT/"dispatch-parity.json").open("w",encoding="utf-8") as f:
        run([python,"-I",LAB/"alpha"/"dispatch_parity.py"],cwd=OUT,stdout=f,env=env)
    with (OUT/"contract-first.json").open("w",encoding="utf-8") as f:
        run([python,"-I",LAB/"alpha"/"contract_first_tests.py"],cwd=OUT,stdout=f,env=env)
    # Static checking in same isolated environment after runtime measurements.
    run([python,"-m","pip","install","mypy==1.15.0"],env=env)
    positive=OUT/"typing_positive.py"
    negative=OUT/"typing_negative.py"
    positive.write_text("from qiskit import QuantumCircuit\nfrom qcontract import Contract, Pauli, prepare, Status\np=prepare(QuantumCircuit(2))\nr=p.check(Contract(requires=Pauli('IZ'), ensures=Pauli('IZ')))\nstatus: Status=r.status\np.verify(p.equivalent_to(p), p.action_matches(p,ancillas=(1,)))\nfrom qcontract import Plan, transition, pauli_on\nplan=Plan((transition('H property', before=pauli_on(2, ((0, 'Z'),)), after='IZ'),))\nplan.verify(p).require()\np.statuses(Contract(requires=pauli_on(2, ((0, 'Z'),)), ensures=Pauli('IZ')))\n",encoding="utf-8")
    negative.write_text("from qiskit import QuantumCircuit\nfrom qcontract import prepare\np=prepare(QuantumCircuit(2))\np.check('not a contract')\n",encoding="utf-8")
    args=[python,"-m","mypy","--strict","--follow-imports=silent","--disable-error-code=import-untyped","--no-incremental"]
    good=run([*args,positive],cwd=OUT,env=env,capture_output=True,text=True)
    bad=subprocess.run([str(x) for x in [*args,negative]],cwd=OUT,env=env,capture_output=True,text=True)
    assert bad.returncode==1 and "[arg-type]" in bad.stdout
    (OUT/"typing.json").write_text(json.dumps({"positive":good.stdout,"negative":bad.stdout,"mypy":"1.15.0"},indent=2),encoding="utf-8")
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    result={"commit":commit,"platform":platform.platform(),"machine":platform.machine(),"python":sys.version,
            "native":{"file":nw.name,"sha256":sha(nw)},"alpha":{"file":pw.name,**audit},
            "smoke":json.loads((OUT/"smoke.json").read_text(encoding="utf-8")),
            "scope":"local wheels, isolated install, no public registry or production compatibility claim"}
    (OUT/"qualification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
if __name__=="__main__":main()
