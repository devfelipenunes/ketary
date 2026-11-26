# Current architecture inventory and maintainability audit

Refs #240 #271 #278 #275 #104. Existing ownership registry (26 runtime
modules) and eager/foundation/private-facade guards remain authoritative.
The enhanced AST inventory records all explicit internal edges, eager
edges, function-local import sites including symbols and line numbers,
SCCs, and cyclic local sites. Every cyclic local edge must have a
reviewed purpose in local-import-rationales.json; reasons describe the
current ownership/use, not dependency inversion or permanent permission.
The old 25-module audit is historical. No new runtime module, new
dependency direction, general backend or second mutable IR.

The inventory reports physical lines, functions/classes, largest
functions and AST branch-node counts (not cyclomatic complexity),
plus exact repeated AST bodies with at least two statements and leading
docstrings removed. Identical syntax is only a review lead: methods
can differ by receiver, binding, context or effect. Do not extract solely
to lower a metric. Previously qualified shared derivative staging #379,
native batch transactions #384 and result ownership #377 demonstrate
coherent private consolidation, not a blanket instruction to split files.

Run:
```sh
python -m research.architecture_inventory > architecture-inventory.json
python -m pytest -q tests/test_architecture_inventory.py tests/test_current_architecture_inventory.py
```
CI records exact current artifact; no assertion that runtime call graph,
dynamic imports, full semantic duplication or independent review are
established. Existing guards must pass; no change to SDK behavior.
