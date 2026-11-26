"""Cross-platform clean wheel/sdist install probes; never publishes."""
import hashlib,json,os,subprocess,sys,tempfile,venv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def run(*args,cwd):
    subprocess.run([str(a) for a in args],cwd=cwd,check=True,timeout=300)

def main():
    rows=[]
    for suffix,extra in (("*.whl",""),("*.whl","[dynamic]"),("*.tar.gz","")):
        paths=list((ROOT/"dist").glob(suffix))
        if len(paths)!=1:raise RuntimeError("expected exactly one distribution")
        artifact=paths[0].resolve()
        with tempfile.TemporaryDirectory(prefix="ketary-platform-") as directory:
            root=Path(directory)
            venv.EnvBuilder(with_pip=True).create(root/"env")
            python=root/"env"/("Scripts/python.exe" if os.name=="nt" else "bin/python")
            run(python,"-m","pip","install",str(artifact)+extra,cwd=root)
            run(python,"-m","pip","check",cwd=root)
            run(python,"-c",'import ketary as q; from pathlib import Path; from importlib.metadata import version; assert version("ketary")=="0.1.0.dev0"; assert Path(q.__file__).resolve().is_relative_to(Path("env").resolve()); assert Path(q.__file__).with_name("py.typed").is_file(); assert Path(q.__file__).with_name("__init__.pyi").is_file(); q.bell().run().test.probability("00", .5).require()',cwd=root)
            if extra:
                run(python,"-c",'import ketary as q; c=q.Circuit.classical(1,1).x(0).measure(0,0); assert c.run_shots(shots=8,seed=1).counts=={"1":8}',cwd=root)
            rows.append({"artifact":artifact.name,"sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"extra":extra,"status":"PASS"})
    (ROOT/"platform-distribution-probe.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
if __name__=="__main__":main()
