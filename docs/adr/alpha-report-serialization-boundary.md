# Candidate ADR — Separate JSON export from verdict semantics

Refs #190 #93 #94. The dictionary-backed report family duplicated identical
to_dict, to_json and render methods in two classes. Share the exact methods
through a private dict subclass, preserving JSON deep-copy behavior, strict
nonfinite rejection, dynamic method dispatch and mutable dict compatibility.
Only _Report adds status/require; SemanticDiffReport remains a set of separate
dimensions with no aggregate verdict. CheckResult and VerificationReport keep
their independent dataclass rendering and bool policies: the apparently
duplicated require bodies do not justify coupling distinct contracts.
No new module/import dependency or public declaration, no runtime speedup
claim; before/after semantics qualified by exact JSON fixtures and existing
report tests. The broader Circuit/ergonomics audit remains open.
