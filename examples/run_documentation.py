"""Execute trusted repository snippets against a clean installed wheel.

Run from the directory containing the copied Markdown files. Not a
general Markdown evaluator and not part of the installed public API.
"""
from pathlib import Path
import re

def main():
    total=0
    for name in ("README.md","getting-started.md","core-api.md","tutorial.md","how-to.md"):
        source=Path(name).read_text(encoding="utf-8")
        shared={"__name__":"__main__"}
        for code in re.findall(r"```python\n([\s\S]*?)\n```",source):
            ns={"__name__":"__main__"} if name in ("tutorial.md","how-to.md") else shared
            exec(compile(code,name,"exec"),ns)
            total+=1
    assert total>0
    print(f"Executed {total} trusted documentation snippets from clean installation")

if __name__=="__main__":
    main()
