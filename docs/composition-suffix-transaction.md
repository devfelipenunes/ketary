# Composition suffix-transaction feasibility

Refs #305 #274 #310. The single independent staging copy had mixed p95
despite lower memory. This separate candidate reuses the native suffix
transaction principle: complete mapping and inverse preparation before
mutation, snapshot an aliased source, append three native blocks, roll back
suffix and phase on ordinary failure. Research only, exact Circuit objects;
no new public dispatch, concurrency guarantee or changed API. Rollback
relies on pinned native append behavior and cannot protect arbitrary
mutation of the existing prefix.

Thirteen cases check alias combinations, phases, late faults, preflight,
and matched full native operators. Three replicates at each prefix length,
same caller-copy cost, current/staged/suffix timings, all raw p50/p95 retained.
No timing gate; dedicated host and isolated memory measurement required
before promotion. No claim of a universal memory or latency improvement.
