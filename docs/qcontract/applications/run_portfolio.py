"""Run all ten portfolio applications against the installed Alpha."""
import json
import pathlib
import runpy
import sys

import qcontract

ROOT = pathlib.Path(__file__).resolve().parent
APPLICATIONS = {
    "communication.py": (
        "ghz_distribution", "graph_resource", "dense_coding",
        "branch_audit", "partition_audit"),
    "logic_and_models.py": (
        "teleportation", "parity_workspace", "compiler_rewrite",
        "hamiltonian_mapping", "noise_transfer"),
}


def main():
    assert sys.flags.isolated
    assert qcontract.__version__ == "0.1.0a3"
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(
        pathlib.Path(sys.prefix).resolve())
    results = {}
    for filename, names in APPLICATIONS.items():
        scope = runpy.run_path(str(ROOT / filename))
        for name in names:
            assert name not in results
            results[name] = scope[name]()
    count = sum(len(r["cases"]) for r in results.values())
    assert len(results) == 10 and count == 46, (len(results),count)
    print(json.dumps({"scope": "author-created bounded ideal application portfolio",
                      "applications": len(results), "fixture_count": count,
                      "results": results}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
