# Pauli query attribution

Refs #306 #307 #256. Isolate native Statevector handle construction from
native Pauli action. Three routes on the same validated immutable snapshot:
public grouped SDK, research fresh native handle per unique label, and
research one native handle per explicit query. The two research paths share
the same validation and numerical result policy. A scalar independent bit
action verifies all outputs before timing. No runtime/API/dependency changes.

Nine workloads: 4/8/12 wires × 1/8/32 distinct full-width canonical labels.
Record alternating randomized route order, raw samples, p50/p95, and maximum
residual. No timing assertions. The public grouped route also supports
weighted Observable inputs; the narrower research routes do not, so do not
infer an API-wide speedup. No persistent cache, mutation, new native backend,
or RSS claim. Dedicated-host repeated benchmark remains required.

Run: python -m research.pauli_query_attribution --output pauli-attribution.json
