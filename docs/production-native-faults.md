# Production backend failure and numerical guard qualification

Fault injection uses synthetic local result objects and a patched transpiler. It establishes fail-closed behavior under declared faults, not native physical backend behavior. Cases cover malformed classical labels, wrong width/trace/PSD, missing Aer, native compiler failures, wrong synthesis, resource caps, invalid statistical evidence and nonfinite complex expectations. Preserve optional real Aer tests. Coverage is measured by the existing exact-head core/dynamic workflow; do not infer an achieved threshold before CI.
