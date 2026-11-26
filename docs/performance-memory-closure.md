# Process-tree memory qualification

Refs #310 #300 #305 #308. Three isolated Linux repetitions for each of
three composition routes at a 10k-gate prefix, and three sweep routes at
14 wires/16 independent tasks. The worker prepares before a handshake,
retains the result through the measurement, then verifies native sequence
or full state before exit. Sweep measures first and second batch with
the same pool; no SDK worker introduced. Parent samples RSS of the worker
and descendants using /proc, recording raw simultaneous sums and own
VmHWM before/after. Shared pages are double counted; sub-sampling can miss
short peaks. Own high-water includes preparation. Not a physical-memory
bound, dedicated-host result, or strict allocator delta. Keep every
replicate. Compare memory and latency together; no promotion if ownership,
rollback, or resource contracts are unproven.
