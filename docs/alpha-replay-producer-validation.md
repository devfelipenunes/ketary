# Replay producer validation — #93 and #190

Replay and evidence share bounded producer metadata validation in _replay. Reject isolated surrogate code points even if JSON-escaped: metadata represents Unicode scalar strings. Valid non-ASCII strings and schema v1 remain supported; no changed caps or artifact hash algorithm. Rejection precedes native circuit allocation. Tests cover nested evidence with recomputed hash, invalid numeric parameters, exact native roundtrip and witness reproduction. No independent security certification.
