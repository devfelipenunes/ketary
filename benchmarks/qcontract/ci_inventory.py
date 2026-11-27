"""Read-only workflow inventory for CI consolidation. No triggers modified."""
import hashlib,json,pathlib,re

ROOT=pathlib.Path(__file__).resolve().parents[2]
def main():
    rows=[]
    for p in sorted((ROOT/".github/workflows").glob("*.yml")):
        raw=p.read_bytes();s=raw.decode()
        if not (p.name.startswith("contract-engine-") or p.name in ("native-contract-engine.yml","native-dependency-audit.yml","qcontract-alpha.yml")):continue
        name=re.search(r"(?m)^name:\s*(.+)$",s).group(1)
        broad="'research/native_contract_engine/**'" in s or '"research/native_contract_engine/**"' in s
        commands=[l.strip() for l in s.splitlines() if re.search(r"python .*?(front_|test_engine|smoke9|benchmark|qualify\.py)|maturin build|cargo audit|pip.audit|platform30",l)]
        kind="required-candidate" if p.name in ("native-dependency-audit.yml","qcontract-alpha.yml") else "historical-review"
        rows.append({"file":p.name,"name":name,"sha256":hashlib.sha256(raw).hexdigest(),
                     "broad_research_trigger":broad,"native_build_mentions":s.count("maturin build"),
                     "commands":commands,"classification":kind,"retirement_approved":False})
    assert len(rows)>=32
    print(json.dumps({"workflow_count":len(rows),"broad_trigger_count":sum(r["broad_research_trigger"] for r in rows),
                      "explicit_native_build_count":sum(bool(r["native_build_mentions"]) for r in rows),
                      "workflows":rows,"scope":"static inventory, not executed-job count or required-check configuration; no deletion"},indent=2))
if __name__=="__main__":main()
