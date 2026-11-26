"""Small reusable state-preparation factories."""
from __future__ import annotations
from ._circuit import Circuit
from ._validation import _int

def bell():
    return Circuit(2).gates.h(0).gates.cx(0,1)

def ghz(n):
    n=_int(n,2)
    c=Circuit(n).gates.h(0)
    for i in range(1,n):
        c.gates.cx(i-1,i)
    return c
