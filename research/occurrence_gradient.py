"""Bounded research derivative of expectation, not an installed gradient API.

Occurrence-wise shifts for one-angle gates with exactly two generator
eigenvalues. Shared native Parameter identity and chain rule are explicit.
Global phase has zero expectation derivative (not zero state derivative).
"""
from collections.abc import Mapping
from math import pi
import numpy as np
import ketary as q
from ketary._validation import _real

_SUPPORTED=frozenset(("rx","ry","rz","rxx","ryy","rzz","p","cp"))

def _numeric(expression,bindings):
    try:
        if getattr(expression,"parameters",()):
            expression=expression.bind({p:bindings[p] for p in expression.parameters})
        value=complex(expression)
    except (TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
        raise ValueError("nonfinite or unbound gradient expression") from exc
    if value.imag!=0:
        raise ValueError("gradient expression must be real")
    return _real(value.real)

def jacobian(c,bindings,observables):
    """Return ordered (observable, native parameter) derivatives and run count."""
    if not isinstance(c,q.Circuit):raise TypeError("expected Circuit")
    if c.num_clbits:raise q.UnsupportedOperation("unitary gradient only")
    params=tuple(c.parameters)
    if c.num_qubits>8 or len(params)>32:
        raise q.ResourceLimit("gradient research width or parameter cap")
    if not isinstance(bindings,Mapping) or set(bindings)!=set(params):
        raise ValueError("complete native parameter identity mapping required")
    vals={p:_real(bindings[p]) for p in params}
    from research.abstraction_primitives import ordered
    obs=ordered(observables,8)
    if any(not isinstance(H,q.Observable) or H.num_qubits>c.num_qubits for H in obs):
        raise ValueError("bounded compatible Observable sequence required")
    raw=c.to_qiskit()
    if len(raw.data)>256:raise q.ResourceLimit("gradient gate cap")
    staged=[]
    for i,item in enumerate(raw.data):
        for j,angle in enumerate(item.operation.params):
            present=getattr(angle,"parameters",())
            if not present:continue
            if item.operation.name not in _SUPPORTED or j!=0:
                raise q.UnsupportedOperation("generator not qualified for two-point shift")
            weights=np.array([_numeric(angle.gradient(p),vals) if p in present else 0. for p in params])
            if np.any(weights):staged.append((i,weights))
    if len(staged)>64:raise q.ResourceLimit("gradient occurrence cap")
    # Complete numeric binding, including symbolic phase, before any run.
    bound=c.bind(vals).to_qiskit()
    # Prepare both validated shifted circuits for every occurrence before simulation.
    pairs=[]
    for index,weights in staged:
        angles=[]
        for sign in (1,-1):
            shifted=bound.copy();item=shifted.data[index]
            gate=item.operation.to_mutable()
            gate.params=[_real(float(gate.params[0])+sign*pi/2)]
            shifted.data[index]=item.replace(operation=gate)
            angles.append(q.from_qiskit(shifted))
        pairs.append((weights,*angles))
    out=np.zeros((len(obs),len(params)))
    for weights,plus,minus in pairs:
        p=plus.run();m=minus.run()
        diff=np.array([.5*(p.math.expectation(H)-m.math.expectation(H)) for H in obs])
        out+=diff[:,None]*weights[None,:]
    if not np.isfinite(out).all():raise ArithmeticError("nonfinite gradient")
    return {"parameters":params,"jacobian":out,"simulation_count":2*len(pairs),
            "scope":"ideal expectation; supported gate occurrences only"}
