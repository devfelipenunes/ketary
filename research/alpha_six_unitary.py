"""Bounded matched studies for #151 #152 #153; no public API changes."""
import inspect,json,random,time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import StatePreparation,DiagonalGate
from qiskit.quantum_info import Operator,Statevector
from research.abstraction_advanced import truth_oracle,_mcx
from research.abstraction_primitives import width,ordered
from research.circuit_rewrite_ladder import metrics,stats

def sdk_basis(label):
    return q.basis(label)

def native_basis(label):
    c=QuantumCircuit(len(label))
    for i,b in enumerate(reversed(label)):
        if b=="1":c.x(i)
    return c

def sdk_product(rows):
    return q.Circuit(len(rows)).ry([a for a,b in rows],range(len(rows))).rz([b for a,b in rows],range(len(rows)))

def native_product(rows):
    c=QuantumCircuit(len(rows))
    for i,(a,b) in enumerate(rows):c.ry(a,i);c.rz(b,i)
    return c

def sdk_dense(v):
    return q.Circuit.prepare_state(v,seed=1101)

def native_dense(v):
    c=QuantumCircuit(len(v).bit_length()-1)
    c.append(StatePreparation(v,normalize=False),range(c.num_qubits))
    return c

def sdk_parity(mask,offset):
    return q.parity_oracle(mask,offset=offset)

def native_parity(mask,offset):
    c=QuantumCircuit(len(mask)+1)
    for i,b in enumerate(reversed(mask)):
        if b=="1":c.cx(i,len(mask))
    if offset:c.x(len(mask))
    return c

def sdk_composed(labels,mask):
    n=len(mask)
    return q.Circuit(n+1).apply(truth_oracle(n,labels)).apply(q.parity_oracle(mask))

def native_composed(labels,mask):
    n=len(mask);c=QuantumCircuit(n+1)
    for label in labels:
        zeros=[i for i,b in enumerate(reversed(label)) if b=="0"]
        if zeros:c.x(zeros)
        c.mcx(range(n),n)
        if zeros:c.x(zeros)
    for i,b in enumerate(reversed(mask)):
        if b=="1":c.cx(i,n)
    return c

def sdk_phase(labels):
    return q.phase_oracle(labels)

def native_phase(labels):
    n=len(labels[0]);diagonal=[-1 if format(i,f"0{n}b") in labels else 1 for i in range(1<<n)]
    c=QuantumCircuit(n);c.append(DiagonalGate(diagonal),range(n))
    return c

def sdk_reflection(v):
    u=sdk_dense(v)
    return q.Circuit(u.num_qubits).apply(u.inverse()).apply(q.phase_oracle("0"*u.num_qubits)).apply(u)

def native_reflection(v):
    u=native_dense(v);n=u.num_qubits
    c=QuantumCircuit(n);c.compose(u.inverse(),inplace=True)
    c.x(range(n));c.h(n-1);c.mcx(range(n-1),n-1);c.h(n-1);c.x(range(n))
    c.compose(u,inplace=True)
    return c

def sdk_amplify(labels,k):
    return q.amplitude_amplification(q.phase_oracle(labels),iterations=k)

def native_amplify(labels,k):
    n=len(labels[0]);c=QuantumCircuit(n);c.h(range(n))
    for _ in range(k):
        c.compose(native_phase(labels),inplace=True)
        c.h(range(n));c.x(range(n));c.h(n-1);c.mcx(range(n-1),n-1);c.h(n-1)
        c.x(range(n));c.h(range(n));c.global_phase+=np.pi
    return c

def cases(seed):
    rng=np.random.default_rng(seed);v=rng.normal(size=4)+1j*rng.normal(size=4);v/=np.linalg.norm(v)
    rows=[(.2,.3),(-.7,.4),(.5,-.8)]
    x=np.array([[0,1],[1,0]],complex);i2=np.eye(2);h=np.array([[1,1],[1,-1]])/np.sqrt(2)
    product=np.ones((1,1),complex)
    for a,b in reversed(rows):
        ry=np.array([[np.cos(a/2),-np.sin(a/2)],[np.sin(a/2),np.cos(a/2)]])
        product=np.kron(product,np.diag([np.exp(-.5j*b),np.exp(.5j*b)])@ry)
    def permutation(n,f):
        d=1<<(n+1);u=np.zeros((d,d),complex)
        for j in range(d):u[j^(int(f(j%(1<<n)))<<n),j]=1
        return u
    labels=("001","110");mask="101";m=int(mask,2)
    phase=np.diag([-1 if format(j,"03b") in labels else 1 for j in range(8)])
    d=2*np.ones((8,8))/8-np.eye(8);uniform=np.kron(np.kron(h,h),h)
    yield "basis",sdk_basis,native_basis,("0101",),np.kron(np.kron(np.kron(i2,x),i2),x),(),()
    yield "product",sdk_product,native_product,(rows,),product,(),()
    yield "dense",sdk_dense,native_dense,(v,),None,(),()
    yield "parity",sdk_parity,native_parity,(mask,1),permutation(3,lambda j:((j&m).bit_count()+1)%2),(),()
    yield "composed",sdk_composed,native_composed,(labels,mask),permutation(3,lambda j:(format(j,"03b") in labels)^bool((j&m).bit_count()%2)),(truth_oracle,_mcx,width,ordered),()
    yield "phase",sdk_phase,native_phase,(labels,),phase,(),()
    yield "reflection",sdk_reflection,native_reflection,(v,),np.eye(4)-2*np.outer(v,v.conj()),(sdk_dense,),(native_dense,)
    yield "amplification",sdk_amplify,native_amplify,(labels,2),np.linalg.matrix_power(d@phase,2)@uniform,(),(native_phase,)

def evaluate(case,seed,reps=3):
    name,sdk,native,args,want,sh,nh=case
    rng=random.Random(seed);routes={"ketary":(sdk,sh),"qiskit":(native,nh)};out={}
    if want is None:
        want=Operator(native(*args)).data
        np.testing.assert_allclose(want[:,0],args[0],atol=1e-9,rtol=0)
        np.testing.assert_allclose(want.conj().T@want,np.eye(len(want)),atol=1e-9,rtol=0)
    g=np.random.default_rng(seed+17)
    v=g.normal(size=len(want))+1j*g.normal(size=len(want));v/=np.linalg.norm(v)
    for key,(fn,helpers) in routes.items():
        c=fn(*args);raw=c.to_qiskit() if key=="ketary" else c
        low=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
        for obj in (raw,low):np.testing.assert_allclose(Operator(obj).data,want,atol=1e-9,rtol=0)
        np.testing.assert_allclose(Operator(raw.inverse()).data,want.conj().T,atol=1e-9,rtol=0)
        source="\n\n".join(inspect.getsource(f) for f in (fn,*helpers))
        out[key]=dict(source=source,metrics=metrics(source),logical_gates=len(raw.data),common_gates=len(low.data),common_depth=low.depth(),build=[],run=[])
    for _ in range(reps):
        for key in rng.sample(list(routes),2):
            fn,_=routes[key];t=time.perf_counter_ns();c=fn(*args);b=time.perf_counter_ns()
            actual=c.run(initial_state=v).math.statevector() if key=="ketary" else Statevector(v).evolve(c).data.copy()
            e=time.perf_counter_ns()
            np.testing.assert_allclose(actual,want@v,atol=1e-9,rtol=0)
            out[key]["build"].append((b-t)/1e6);out[key]["run"].append((e-b)/1e6)
    for row in out.values():
        for k in ("build","run"):row[k]=stats(row[k])
    extra={}
    if name=="amplification":
        labels,k=args;theta=np.arcsin(np.sqrt(len(labels)/len(want)))
        probability=sum(abs(want[int(s,2),0])**2 for s in labels)
        np.testing.assert_allclose(probability,np.sin((2*k+1)*theta)**2,atol=1e-9,rtol=0)
        extra["marked_probability"]=float(probability)
    return dict(name=name,seed=seed,paths=out,**extra)

def run(reps=3):
    return [evaluate(case,seed,reps) for seed in (1101,2202,3303) for case in cases(seed)]

if __name__=="__main__":
    print(json.dumps({"scope":"strict bounded operators and complex states; dense extension compared to native, independent zero-column oracle; authored helpers included, installed internals excluded; shared CI diagnostic","rows":run()},indent=2,allow_nan=False))
