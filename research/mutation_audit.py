"""Targeted source mutation audit in disposable copies, never the checkout.

Classifies killed/survived/invalid explicitly. These hand-selected mutants
are not a repository-wide mutation score or an equivalence classifier.
"""
import argparse,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
MUTANTS=(
    ("erase_evolution_phase","src/ketary/_ergonomics.py","native.global_phase=phase","native.global_phase=0.0","tests/test_symbolic_evolution.py"),
    ("reverse_embedding","src/ketary/_observable.py","axes[n-1-w]=label[k-1-i]","axes[n-1-w]=label[i]","tests/test_observable_on.py"),
    ("ignore_imaginary_nan","src/ketary/_result.py","not math.isfinite(value.imag) or ","","tests/test_native_expectation_boundary.py"),
    ("borrow_mutable_plan_source","src/ketary/_plan.py","snapshot=Circuit.from_json(payload)","snapshot=circuit","tests/test_query_plan_snapshot.py"),
)

def run(root,test,tag):
    env=os.environ.copy();env["PYTHONPATH"]=str(root/"src");env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
    # Verify import resolution in the subprocess before any test.
    check=subprocess.run([sys.executable,"-c","import ketary,pathlib; print(pathlib.Path(ketary.__file__).resolve())"],cwd=root,env=env,capture_output=True,text=True,timeout=30)
    if check.returncode or not check.stdout.strip().startswith(str(root/"src/ketary")+os.sep):
        return dict(status="invalid",detail="unexpected import origin",log=check.stdout+check.stderr)
    xml=root/(tag+".xml")
    proc=subprocess.run([sys.executable,"-m","pytest","-q",test,"--junitxml",str(xml)],
                        cwd=root,env=env,capture_output=True,text=True,timeout=180)
    if not xml.exists():return dict(status="invalid",returncode=proc.returncode,log=proc.stdout+proc.stderr)
    tree=ET.parse(xml);cases=list(tree.iter("testcase"))
    failures=[c.attrib.get("name","") for c in cases if c.find("failure") is not None]
    errors=[c.attrib.get("name","") for c in cases if c.find("error") is not None]
    skipped=[c.attrib.get("name","") for c in cases if c.find("skipped") is not None]
    status="pass" if proc.returncode==0 and cases and not skipped else "failure" if proc.returncode==1 and failures and not errors else "invalid"
    return dict(status=status,returncode=proc.returncode,cases=len(cases),failures=failures,errors=errors,skips=skipped,log=proc.stdout+proc.stderr)

def evaluate(mutant):
    name,path,old,new,test=mutant
    with tempfile.TemporaryDirectory(prefix="ketary-mutation-") as d:
        root=Path(d)/"checkout"
        shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns(".git",".venv","__pycache__",".pytest_cache",".mypy_cache","dist","build","*.egg-info",".coverage*"))
        target=root/path;source=target.read_text()
        if source.count(old)!=1:return dict(name=name,status="invalid",detail="mutation anchor must occur once")
        baseline=run(root,test,"baseline")
        if baseline["status"]!="pass":return dict(name=name,status="invalid",baseline=baseline)
        target.write_text(source.replace(old,new,1))
        # Avoid timestamp/size bytecode cache reuse after source substitution.
        for cache in (root/"src").rglob("__pycache__"):shutil.rmtree(cache)
        changed=run(root,test,"mutant")
        if changed["status"]=="failure":status="killed"
        elif changed["status"]=="pass":status="survived"
        else:status="invalid"
        return dict(name=name,status=status,baseline=baseline,mutant=changed)

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    rows=[]
    for m in MUTANTS:
        try:row=evaluate(m)
        except subprocess.TimeoutExpired:row=dict(name=m[0],status="invalid",detail="subprocess timeout")
        rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ("baseline","mutant")}),flush=True)
    a.output.write_text(json.dumps(dict(scope="four hand-selected non-equivalent intended defects; no overall mutation score",rows=rows),indent=2))
    if any(r["status"]=="invalid" for r in rows):raise SystemExit(1)
if __name__=="__main__":main()
