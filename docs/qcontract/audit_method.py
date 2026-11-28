"""Audit methodology evidence inventory after all installed-wheel exercises."""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
ARTIFACTS = {
    "contract-review-rounds.json": ("R1_sufficiency", "R2_minimality", "R3_composition",
                                    "R4_evolution", "R5_diagnostics"),
    "contract-workflow-rounds.json": ("R6_authoring", "R7_ergonomics", "R8_admission",
                                      "R9_traceability", "R10_evidence_gate"),
    "contract-practical-rounds.json": ("R11_algorithm", "R12_modularity",
                                      "R13_parameterized_authoring", "R14_agent_handoff"),
    "contract-project-rounds.json": ("R16_expressivity", "R17_modules",
                                    "R18_architecture", "R19_ergonomics"),
}
DOCS = ("README.md", "contract-design.md", "pattern-review.md", "five-review-rounds.md",
        "workflow-rounds.md", "practical-guide.md", "method-v1.md", "method-evaluation.md",
        "ten-cycle-roadmap.md", "project_example/requirements.py",
        "project_example/implementation.py", "project_example/verify.py")


def main():
    assert len(sys.argv) == 2
    evidence_dir = pathlib.Path(sys.argv[1])
    inventory = {}
    for filename, expected in ARTIFACTS.items():
        payload = json.loads((evidence_dir / filename).read_text(encoding="utf-8"))
        assert isinstance(payload["scope"], str) and payload["scope"]
        results = payload["results"]
        assert set(results) == set(expected), (filename, set(results))
        assert all(isinstance(results[key], dict) and results[key] for key in expected)
        inventory[filename] = list(expected)
    for filename in DOCS:
        assert (ROOT / filename).is_file(), filename
    # R15 and R20 are documentation/integration reviews, not engine tests.
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                  cwd=ROOT, text=True).strip()
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)
    print(json.dumps({"commit": sha, "evidence_inventory": inventory,
                      "executable_rounds": sum(map(len, inventory.values())),
                      "documentation_rounds": ["R15", "R20"],
                      "required_files": list(DOCS),
                      "scope": "inventory of same-job evidence, not independent scientific evaluation"},
                     indent=2))


if __name__ == "__main__":
    main()
