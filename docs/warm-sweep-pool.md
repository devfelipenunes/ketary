# Warm-pool sweep amortization

Refs #308 #301. Follow-up to the cold-pool #386 results. Four bounded
workloads (10/14 wires, 4/16 tasks); serial versus two explicit reusable
threads and two spawn processes. Record first batch and teardown separately
from warm batches. Process tasks still replay validated JSON and return full
ordered arrays. Every measured result checked against the native reference;
source snapshots unchanged. Pools are scoped to the research function, not
the SDK. No hidden worker, global cache, thread-safety promise, or memory
guarantee. Retained array bytes exclude aggregate child-process RSS.
Do not compare warm time with cold time as identical semantics. Dedicated
host and lifecycle/resource review required before any API proposal.
