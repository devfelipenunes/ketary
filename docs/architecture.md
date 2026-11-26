# Experimental modular architecture

The public package is a facade. QuantumCircuit is the authoritative mutable
program; Result owns a defensive ideal-state snapshot. No parallel mutable IR,
new backend, or custom simulator is introduced.

| Module | Responsibility | Internal dependencies |
|---|---|---|
| _validation | integer, tolerance, memory guards, exceptions | NumPy |
| _adapter | strict Qiskit import validation and lazy SDK loading | _validation |
| _result | independent snapshots, sampling, math, checks | _validation |
| _trace | explicit bounded state evolution | _adapter, _result, _validation |
| _circuit | builder, gates, transforms, run | _adapter, _result, _trace, _validation |
| _algorithms | Bell and GHZ factories | _circuit, _validation |

The package exports the same public objects. The previous private _limit
binding is retained for existing internal tests, not part of the supported
public API. The package uses a src layout; new gates and parameter support are separate increments.
Validate all existing tests, facade imports and paired benchmarks before
accepting the modularization. The production gate and human usability
evaluation remain separate requirements. Python 3.12.x only.

The PoC and modular refactor are merged into main. The package remains experimental.
