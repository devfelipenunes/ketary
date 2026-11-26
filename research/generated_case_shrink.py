"""Explicit deterministic shrink of an ordered-unitary generated counterexample.

No automatic shrinking claim for other generated families. No runtime change.
"""
import numpy as np
import ketary as q

def minimize(items, fails, *, max_attempts=128):
    if type(max_attempts) is not int or not 1<=max_attempts<=128:
        raise ValueError("attempt budget must be 1..128")
    if not isinstance(items,(tuple,list)) or len(items)>64:
        raise ValueError("bounded sequence required")
    current=tuple(items)
    if not fails(current):raise ValueError("initial example does not reproduce failure")
    attempts=0;index=0
    while index<len(current) and attempts<max_attempts:
        candidate=current[:index]+current[index+1:]
        attempts+=1
        if fails(candidate):current=candidate;index=0
        else:index+=1
    return dict(items=current,attempts=attempts,local_minimal=index==len(current))

def ordered_case(seed):
    if type(seed) is not int or not 0<=seed<250:raise ValueError("seed outside corpus")
    rng=np.random.default_rng(25001+seed)
    n=int(rng.integers(1,5));v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    rows=[]
    for _ in range(int(rng.integers(5,19))):
        w=int(rng.integers(n));kind=int(rng.integers(6));theta=float(rng.uniform(-4,4))
        if kind==0:rows.append(("h",(w,),0.))
        elif kind==1:rows.append(("x",(w,),0.))
        elif kind==2:rows.append(("ry",(w,),theta))
        elif kind==3:rows.append(("rz",(w,),theta))
        elif kind==4 and n>1:rows.append(("cx",(w,(w+int(rng.integers(1,n)))%n),0.))
        else:rows.append(("p",(w,),theta))
    return n,v,tuple(rows),float(rng.uniform(-3,3))

def check(n,v,rows,phase,*,defect=False):
    I=np.eye(2, dtype=complex);X=np.array([[0,1],[1,0]],complex)
    Y=np.array([[0,-1j],[1j,0]],complex);Z=np.diag([1.,-1.]);H=(X+Z)/np.sqrt(2)
    c=q.Circuit(n);U=np.eye(1<<n,dtype=complex)
    def embed(M,w):
        out=np.ones((1,1),complex)
        for wire in reversed(range(n)):out=np.kron(out,M if wire==w else I)
        return out
    for name,wires,t in rows:
        w=wires[0]
        if name=="cx":
            target=wires[1];c.cx(w,target)
            G=np.zeros_like(U)
            for j in range(1<<n):G[j^(((j>>w)&1)<<target),j]=1
        else:
            if name in ("h","x"):
                getattr(c,name)(w);M=H if name=="h" else X
            elif name=="p":
                # Deliberate sign fault for qualification only.
                c.p(-t if defect else t,w);M=np.diag([1,np.exp(1j*t)])
            else:
                getattr(c,name)(t,w);P=Y if name=="ry" else Z
                M=np.cos(t/2)*I-1j*np.sin(t/2)*P
            G=embed(M,w)
        U=G@U
    c.evolve(q.I(n-1),time=phase);U=np.exp(-1j*phase)*U
    got=c.run(initial_state=v).math.statevector()
    inverse=c.inverse().run(initial_state=got).math.statevector()
    return max(float(np.max(np.abs(got-U@v))),float(np.max(np.abs(inverse-v))),abs(float(np.vdot(got,got).real)-1.))<=1e-9
