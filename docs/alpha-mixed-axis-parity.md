# Mixed-axis shared parity — #154 and #303

The installed diagonal parity reuse is already profiled by
research/alpha_parity_profile.py. This candidate investigates a strictly
smaller subset of general commuting Hamiltonians: every wire has a common
nonidentity Pauli axis across terms. One common basis change maps the sum to
Z strings; reuse the existing diagonal evolution and uncompute. Identity
terms retain global phase, Y uses S-dagger/H then H/S. No hidden ancillas,
measurement or new public API. General commuting XX and ZZ do not satisfy
the restriction; retain the existing route for such operators.

Compare full dense expm, arbitrary complex inputs, reversed placement,
native PauliEvolutionGate, and identical common-basis gates/depth. Three
seeds, five repetitions; build and native execution measured separately.
No equal-lowering-cost, RSS or controlled-host claim. Promote only if
strict semantic and cost evidence supports it; symbolic admission, zero
time and gate budgets require further tests before runtime promotion.
