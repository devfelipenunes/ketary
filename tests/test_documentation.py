"""Execute standalone Python snippets from trusted checked-in documentation."""
from pathlib import Path
import re
import pytest

ROOT=Path(__file__).resolve().parents[1]
CASES=[]
for filename in ("tutorial.md","how-to.md"):
    source=(ROOT/"docs"/filename).read_text(encoding="utf-8")
    for i,code in enumerate(re.findall(r"```python\n([\s\S]*?)\n```",source)):
        CASES.append(pytest.param(code,id=f"{filename}:{i+1}"))

@pytest.mark.parametrize("code",CASES)
def test_documented_example(code):
    exec(compile(code,"<trusted repository documentation>","exec"),{"__name__":"__main__"})
