# Expressive composition: staging cost attribution

Refs #256 #304 #305 #345. Current compute_action_uncompute builds three
independent composed prefixes before committing. This research route copies
the prefix once and stages three native compositions on that independent
copy. No runtime changes. Test strict operator equality including phase,
self-alias source ownership, net checkpoint behavior and late native faults.
The public implementation supports more dispatch/validation circumstances;
the research route is bounded, not a universal drop-in replacement.

Three prefixes (32, 1000, 10000 gates), identical caller-owned copy in both
routes, full operator comparison before timing, randomized paired order,
warm-up and raw p50/p95. No noisy timing assertions or general speedup
claim. Prefix length is not circuit width. Current runner is shared, RSS
and broader validation remain prerequisites for any runtime adoption.

Run: python -m research.expressive_composition_cost --output composition-cost.json
