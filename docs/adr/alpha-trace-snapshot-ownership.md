# Candidate ADR — Reuse owned native checkpoint snapshots

Status: proposed in #473; do not treat as accepted before exact-head CI,
independent prefix and alias tests, and paired performance review.

Context: the monotonic trace cursor formerly copied every checkpoint's
amplitude array into Result. The pinned Qiskit ideal evolution path already
supports transferring a fresh exclusively owned native output.

Decision: reuse Result._from_evolution for trace checkpoints. A fresh
contiguous writable owned array can be adopted and frozen; views, read-only
arrays and repeated checkpoints fall back to copying. The cursor continues
native evolution out-of-place from its read-only state. No persistent cache
or cross-call state, new module or import dependency.

Consequences: avoid a full defensive copy where the existing ownership
predicate admits transfer. Each retained Result remains independent and
immutable. Native evolution, per-checkpoint normalization and finite-value
validation, exact phase, ordered wires and existing payload/step limits are
unchanged. The cursor retains only its current state. No process RSS or
general acceleration claim; verify raw matched timings and ownership tests.
