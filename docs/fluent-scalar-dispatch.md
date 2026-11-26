# Fluent scalar dispatch diagnostic

Refs #304 #256 #345. Exact builtin int wire and builtin int/float rotation
angle calls avoid local import, iterable detection and indirect getattr
before reaching the same validated _Gates implementation. All other values
retain the previous path, including bool rejection, numeric subclasses,
symbolic and aligned/broadcast batches. No native or resource policy change.

81 parameterized regression cases compare native sequence and strict
operators, symbolic binding, nonbuiltin inputs, errors and ownership.
Benchmark mixed 1k/10k gates: previous method bodies in a subclass versus
candidate facade and native Qiskit, same operations and validation, ordered
circuit equality before randomized paired timing, raw median/p95. The
subclass baseline is an attribution comparator, not a full old-revision
benchmark; shared runner and no RSS/production claim.
