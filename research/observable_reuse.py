"""Research-only local observable embedding and reuse; no installed API."""
from collections.abc import Mapping
from itertools import islice
import ketary as q
from ketary._validation import _int

def embed(observable,wires,*,width):
    """Local bit i maps to wires[i]; no hidden ancillas or simulation."""
    if not isinstance(observable,q.Observable):raise TypeError("expected Observable")
    n=_int(width,1)
    if n>62:raise q.ResourceLimit("embedding width exceeds 62")
    if isinstance(wires,(str,bytes,Mapping,set,frozenset)):raise ValueError("ordered wires required")
    k=observable.num_qubits
    try:ws=tuple(_int(w) for w in islice(iter(wires),k+1))
    except TypeError as exc:raise ValueError("ordered wires required") from exc
    if len(ws)!=k or len(set(ws))!=k or any(w>=n for w in ws):
        raise ValueError("exact distinct local-to-global wire mapping required")
    out={}
    for label,coef in observable.to_dict().items():
        axes=["I"]*n
        for i,w in enumerate(ws):axes[n-1-w]=label[k-1-i]
        out["".join(axes)]=coef
    return q.Observable(out)

def local_evolution(c,H,time,*,wires):
    """Use the existing evolve/apply grammar; returns same Circuit."""
    return c.evolve(embed(H,wires,width=c.num_qubits),time=time)
