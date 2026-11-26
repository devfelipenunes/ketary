# Combined Rust → QuEST native execution

The research C API extension now supports a separate QuEST-compatible
read-only packing entry point for 11 standard gates. The existing eight
gate construction benchmark is unchanged. The new packing path borrows
native CircuitData with the GIL held and emits bounded native-endian
bytes. NumPy views consume those bytes without per-gate object conversion.
The QuEST bridge invokes the existing specialized C++ kernels, preserving
strict phase and wire order. No raw pointers escape, no second persistent
circuit model, no public API change. Exact basis checks include every
supported gate and reject custom/open-control/unbound/classical modes.
Compare Python and C API packing and end-to-end execution independently
on one shared runner. This is an experimental subset, not full SDK support.
