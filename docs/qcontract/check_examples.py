"""Execute the actual documented Python blocks against an installed Alpha.

Run from a fresh qualified venv with python -I, never an editable install.
Each document has its own namespace; blocks within it run in page order.
These are trusted repository examples, not a general Markdown executor.
"""
import contextlib
import io
import json
import pathlib
import re
import sys

ROOT=pathlib.Path(__file__).resolve().parent
EXPECTED={"tutorial.md":4,"how-to.md":1,"methodology.md":4,"testing.md":2,"practice.md":3}

def main():
    import qcontract
    assert qcontract.__version__=="0.1.0a3"
    assert sys.flags.isolated
    assert pathlib.Path(qcontract.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())
    rows=[]
    for name,count in EXPECTED.items():
        source=(ROOT/name).read_text(encoding="utf-8")
        blocks=re.findall(r"^\x60\x60\x60python\s*\n(.*?)^\x60\x60\x60\s*$",source,re.MULTILINE|re.DOTALL)
        assert len(blocks)==count,(name,len(blocks),count)
        scope={"__name__":"__qcontract_doc_example__"}
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            for index,code in enumerate(blocks,1):
                exec(compile(code,f"{name}:block-{index}","exec"),scope)
            if name=="how-to.md":
                scope["test_bell_contract"]()
        rows.append({"document":name,"executed_blocks":len(blocks),"captured_output":output.getvalue(),"status":"PASS"})
    print(json.dumps({"version":qcontract.__version__,"documents":rows,"blocks":sum(x["executed_blocks"] for x in rows)},indent=2,allow_nan=False))

if __name__=="__main__":
    main()
