"""Shared input validation and resource guards."""
from __future__ import annotations
import math
import operator
from numbers import Real
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

def _real(value):
    if isinstance(value,(bool,np.bool_)) or not isinstance(value,Real):
        raise ValueError("expected a finite real number")
    try:
        result=float(value)
    except (OverflowError,ValueError,TypeError) as exc:
        raise ValueError("expected a finite real number") from exc
    if not math.isfinite(result):
        raise ValueError("expected a finite real number")
    return result

def _tol(value):
    value = _real(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError("invalid tolerance")
    return value

def _angle(value):
    if isinstance(value,(bool,np.bool_)) or not isinstance(value,Real):
        raise ValueError("rotation angle must be a finite real number in radians")
    try:
        angle=float(value)
    except (ValueError,OverflowError,TypeError) as exc:
        raise ValueError("invalid rotation angle") from exc
    if not math.isfinite(angle):
        raise ValueError("rotation angle must be finite")
    return angle
