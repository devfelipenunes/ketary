# ADR 002 — One public facade, selective adapter boundaries

Status: implemented design, documented retrospectively.

Context: a Python library must be simple to learn and maintain while keeping
optional integrations isolated.

Decision: one public import and progressive access through existing objects.
Keep responsibilities in private modules; _adapter handles native validation,
_classical owns optional Aer, _external owns optional QCEC. Keep native
representation authoritative. Do not mandate dependency injection, abstract
backend protocols or separate domain/application/infrastructure packages.

Alternatives: fully hexagonal backend-independent architecture; unstructured
single module; new high-level facade. These do not serve the current scope.

Consequences: selected Ports & Adapters principles apply; direct native
imports and local back-references remain. Track dependencies and revisit
only when a concrete requirement warrants a boundary. The SDK is not a
strict hexagonal implementation.
