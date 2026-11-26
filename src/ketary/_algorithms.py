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


def constant_oracle(n, *, value=0):
    """Construct U_f for f(x)=value, with the target on wire n."""
    n=_int(n,1)
    value=_int(value)
    if value not in (0,1):
        raise ValueError("constant value must be 0 or 1")
    c=Circuit(n+1)
    if value:
        c.gates.x(n)
    return c

def parity_oracle(mask, *, offset=0):
    """Construct U_f for f(x)=a·x XOR offset, a nonzero binary mask.

    The rightmost character denotes input wire zero. Target is wire len(mask).
    """
    if not isinstance(mask,str) or not mask or any(b not in "01" for b in mask) or "1" not in mask:
        raise ValueError("mask must be a nonzero binary string")
    offset=_int(offset)
    if offset not in (0,1):
        raise ValueError("offset must be 0 or 1")
    c=Circuit(len(mask)+1)
    for i,bit in enumerate(reversed(mask)):
        if bit=="1":
            c.gates.cx(i,len(mask))
    if offset:
        c.gates.x(len(mask))
    return c

def deutsch_jozsa(oracle):
    """Build the Deutsch-Jozsa circuit for an explicit bit-flip oracle.

    Caller promises U_f|x,y> = |x,y XOR f(x)> with constant or balanced f.
    The last wire is the target; all lower wires hold the input register.
    This function does not prove the promise or execute the circuit.
    """
    if not isinstance(oracle,Circuit):
        raise TypeError("expected Circuit oracle")
    n=oracle.num_qubits-1
    if n<1:
        raise ValueError("oracle requires at least one input and one target")
    c=Circuit(n+1).gates.x(n)
    for i in range(n+1):
        c.gates.h(i)
    c=c.compose(oracle)
    for i in range(n):
        c.gates.h(i)
    return c
