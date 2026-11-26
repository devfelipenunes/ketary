"""Execute trusted checked-in notebook code without Jupyter dependencies."""
import json
from pathlib import Path

def test_quantum_engineering_notebook():
    path=Path(__file__).resolve().parents[1]/"examples"/"quantum_engineering.ipynb"
    notebook=json.loads(path.read_text(encoding="utf-8"))
    scope={"__name__":"__main__"}
    for cell in notebook["cells"]:
        if cell["cell_type"]=="code":
            exec(compile("".join(cell["source"]),str(path),"exec"),scope)
