"""Ordered logical connection patterns, not a hardware coupling map."""
from collections.abc import Mapping
from itertools import islice, combinations
from ._validation import _int, ResourceLimit

def _wires(wires,minimum=2):
    if isinstance(wires,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered distinct wire indices")
    try:
        values=tuple(_int(w) for w in islice(iter(wires),4097))
    except TypeError as exc:
        raise ValueError("expected ordered distinct wire indices") from exc
    if len(values)>4096:
        raise ResourceLimit("topology supports at most 4096 wires")
    if len(values)<minimum or len(set(values))!=len(values):
        raise ValueError(f"topology requires at least {minimum} distinct wires")
    return values

def chain(wires):
    """Consecutive directed pairs in caller order."""
    values=_wires(wires)
    return tuple(zip(values,values[1:]))

def ring(wires):
    """Directed chain closed by the last-to-first edge; >=3 wires."""
    values=_wires(wires,3)
    return tuple(zip(values,values[1:]+values[:1]))

def star(wires):
    """First wire is the center; directed center-to-leaf pairs."""
    values=_wires(wires)
    return tuple((values[0],w) for w in values[1:])

def all_pairs(wires):
    """One pair per unordered combination, oriented by caller order."""
    values=_wires(wires)
    if len(values)*(len(values)-1)//2>10000:
        raise ResourceLimit("topology supports at most 10000 pairs")
    return tuple(combinations(values,2))
