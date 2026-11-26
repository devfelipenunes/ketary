# Bounded batch ingestion

Refs #304 #305 #256. Exact immutable tuple pairs bypass iterator materialization
and abstract collection classification; all wire validation still uses
_Gates._pair. Exact Circuit selection reuses one ephemeral gate wrapper
rather than one per element. Subclass and generic iterable paths retain
previous dispatch, bounded consumption and validation. No public API, native
mutation or resource cap changes.

27 parameterized regression cases cover strict native sequence, mapped
operators, invalid and unbounded inputs, symbolic selections and subclass
dispatch. Four paired 800/8000-gate construction diagnostics patch only
previous ingestion bodies outside the timed sections, retaining identical
native broadcast and rollback. Raw p50/p95; no universal speedup claim.
