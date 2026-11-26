# Copy and intermediate object inventory

Issue #276. Combine the existing statevector-ownership, binding,
query-plan and process-tree RSS studies with direct attribution of
logical serialization/replay, native export, circuit copy, symbolic
binding, execution and snapshot export. Three templates (4/8/12
wires) x seven operations x three isolated Linux repetitions. Exact
native circuit equality or complete complex state checked after
measurement; mutate exported copies to verify source isolation.
Seven smoke regression cases. Raw p50/p95 and own VmHWM before/after;
report retained JSON UTF-8 bytes, numeric array payload bytes and
native instruction count separately. Native object counts are not
native heap byte sizes; HWM includes preparation, and its increment
is not an exact transient allocation total. No runtime change, no
new ownership claim and no dedicated-host claim.

| Route | Retained result | Intermediate work |
|---|---|---|
| Circuit.copy | independent native circuit | native copy and annotations |
| to_qiskit | independent native circuit | native copy |
| to_json | bounded logical UTF-8 text | validation, instruction dictionaries, encoder |
| from_json | independent native circuit | parsed fields, validation, native construction |
| bind | independent bound circuit | validated bindings, native assignment and numeric scan |
| run | defensive statevector snapshot | native evolution and adoption/copy |
| statevector | independent array | defensive export copy |

See resource-contracts.md, statevector_ownership.py, native_stage_profile.py,
query_plan_cost.py and performance_memory_closure.py for related evidence.
