"""Static checks for the required exact-head CI contract (#95/#198)."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def test_required_workflow_contract():
    source=(ROOT/".github/workflows/validate.yml").read_text()
    assert re.search(r"(?m)^  pull_request:\s*$",source)
    assert re.search(r"(?m)^  push:\s*\n    branches: \[main\]",source)
    assert "contents: read" in source
    jobs=re.split(r"(?m)^  ([a-z][a-z-]*):\s*\n",source.split("\njobs:\n",1)[1])
    sections=dict(zip(jobs[1::2],jobs[2::2],strict=True))
    assert set(sections)=={"tests","dynamic","dependency-review","external-verifier","benchmark","packaging"}
    for name,body in sections.items():
        assert "timeout-minutes:" in body,name
        assert "persist-credentials: false" in body,name
        assert "github.event.pull_request.head.sha || github.sha" in body,name
        for use in re.findall(r"(?m)^\s*- uses: ([^\s#]+)",body):
            assert re.fullmatch(r"[^@]+@[0-9a-f]{40}",use),use
    for name in ("tests","dynamic"):
        assert "--fail-under=95" in sections[name]
        assert "--junitxml=" in sections[name]
        assert "coverage json" in sections[name]
    assert "pip_audit" in sections["dependency-review"]
    assert "twine check" in sections["packaging"]
    assert "peak RSS" in sections["benchmark"]
    assert "tests_external" in sections["external-verifier"]
