# Variational shared-parameter workflow

Refs #283 #285 #248 #345 #211 #254. One product-state family with twelve
parameter variants and three negative controls; not twelve independent
scientific application intents. Tests use one symbolic layer placed twice,
native parameter identities, an asymmetric additional rotation, explicit
global phase, two real observables and a reusable contract. Independent
closed-form product state/derivatives and a matched native operator are
separate oracles. No API growth or automatic optimizer.

The expressive route is intentionally ordinary Python:
```python
import ketary as q
a,b=q.Circuit.parameter_vector("p",2)
layer=q.Circuit.symbolic(1).ry(a+b,0)
c=q.Circuit.symbolic(3).apply_each(layer,wires=[0,2])
c.ry(.2*b,1)
H=(q.Z(0)+q.Z(2))*.5
K=q.Z(1)
point={a:.37,b:-.62}
energy=c.bind(point).run().math.expectations([H,K])
J=c.expectation_jacobian(point,[H,K])
hessian=c.expectation_hessian(point,[H,K])
metric=c.quantum_geometric_tensor(point)
```

No claim of shorter source than all native alternatives, independent human
or AI usability, or performance improvement. CI must validate actual API
spelling and parameter order. Near-null conditioning cases are explicit;
no inverse metric or regularization is implicit.
