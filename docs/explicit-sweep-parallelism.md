# Explicit sweep concurrency feasibility

Refs #308 #102 #103 #301. Six bounded workloads, 6/10/14 wires and 4/16
independent fully bound circuits. Two worker threads or two spawn processes
versus serial execution. No mutable circuit is shared between tasks.
Process tasks reconstruct strict logical JSON. Pool setup/teardown and
transport are included in timings; preparation of independent tasks and
payloads is outside timing, so not a full end-to-end sweep benchmark.
All routes return ordered independent complex arrays and are compared to
native Qiskit reference before timing. Record raw p50/p95 and retained
output bytes, not aggregate process RSS. Explicit workers and BLAS thread
limits, no hidden parallelism, scheduler, API, SDK thread-safety claim or
new execution backend. Repeated pool and process-memory measurements on
an authorized dedicated host are still necessary before any adoption.
