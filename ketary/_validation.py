"""Shared input validation and resource guards."""
from __future__ import annotations
import math
import operator
import numpy as np

class UnsupportedOperation(ValueError):
    pass

class ResourceLimit(ValueError):
    pass

def _int(value, minimum=0):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("expected an integer, not bool")
    try:
        value = operator.index(value)
    except TypeError as exc:
        raise ValueError("expected an integer") from exc
    if value < minimum:
        raise ValueError(f"expected integer >= {minimum}")
    return value

def _limit(n, snapshots=1, budget=64*1024**2):
    budget = _int(budget, 1)
    # Payload only; not a guarantee of total process RSS.
    if n > 62 or 16 * (1 << n) * snapshots > budget:
        raise ResourceLimit("dense statevector payload exceeds budget")

def _tol(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError("invalid tolerance")
    return value
