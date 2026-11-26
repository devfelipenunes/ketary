"""Matched local ideal and IID repetition-code application diagnostics."""
import inspect,itertools,json,time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.quantum_info import DensityMatrix,Statevector,Kraus,Operator
from research.circuit_rewrite_ladder import metrics,stats

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Z=np.diag([1.,-1.]).astype(complex)

def channel(p,phase):
    matrices=[]
    for bits in itertools.product((0,1),repeat=3):
        weight=p**sum(bits)*(1-p)**(3-sum(bits))
        op=np.array([[1.]],complex)
        for bit in reversed(bits):op=np.kron(op,(Z if phase else X) if bit else I)
        matrices.append(np.sqrt(weight)*op)
    return Kraus(matrices)

def sdk_recovery(theta,phi,phase):
    enc=q.Circuit(3).ry(theta,0).rz(phi,0).cx(pairs=[(0,1),(0,2)])
    dec=q.Circuit(3)
    if phase:enc.h(range(3));dec.h(range(3))
    dec.cx(pairs=[(0,2),(0,1)]).ccx(1,2,0)
    return enc,dec

def native_recovery(theta,phi,phase):
    enc=QuantumCircuit(3);enc.ry(theta,0);enc.rz(phi,0);enc.cx(0,[1,2])
    dec=QuantumCircuit(3)
    if phase:enc.h(range(3));dec.h(range(3))
    dec.cx(0,[2,1]);dec.ccx(1,2,0)
    return enc,dec

def sdk_syndrome(theta,phi,error):
    c=q.Circuit(5).ry(theta,0).rz(phi,0).cx(pairs=[(0,1),(0,2)])
    if error is not None:c.x(error)
    return c.cx(pairs=[(0,3),(1,3),(0,4),(2,4)])

def native_syndrome(theta,phi,error):
    c=QuantumCircuit(5);c.ry(theta,0);c.rz(phi,0);c.cx(0,[1,2])
    if error is not None:c.x(error)
    c.cx([0,1,0,2],[3,3,4,4])
    return c

def resource(circuits,mode):
    if not isinstance(circuits,tuple):circuits=(circuits,)
    raws=[c.to_qiskit() if mode=="sdk" else c for c in circuits]
    lower=[transpile(c,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=1101,qubits_initially_zero=False) for c in raws]
    for a,b in zip(raws,lower,strict=True):
        np.testing.assert_allclose(Operator(a).data,Operator(b).data,atol=1e-9,rtol=0)
    return {"logical_gates":sum(len(c.data) for c in raws),"common_basis_gates":sum(len(c.data) for c in lower),
            "common_basis_depth_sum":sum(c.depth() for c in lower)}

def evaluate(family,theta,phi,arg,reps=3):
    v=np.array([np.exp(-.5j*phi)*np.cos(theta/2),np.exp(.5j*phi)*np.sin(theta/2)])
    rho=np.outer(v,v.conj())
    if family=="syndrome":
        builds={"sdk":sdk_syndrome,"native":native_syndrome};args=(theta,phi,arg)
        syndrome={None:0,0:3,1:1,2:2}[arg];mask=0 if arg is None else 1<<arg
        expected=np.zeros(32,complex)
        expected[(syndrome<<3)|mask]=v[0];expected[(syndrome<<3)|(7^mask)]=v[1]
    else:
        phase=family=="phase";p=arg
        builds={"sdk":sdk_recovery,"native":native_recovery};args=(theta,phi,phase)
        noise=channel(p,phase);failure=3*p*p-2*p**3
        expected=(1-failure)*rho+failure*X@rho@X
    paths={}
    for mode,fn in builds.items():
        source=inspect.getsource(fn)
        paths[mode]={"source":source,"metrics":metrics(source),**resource(fn(*args),mode),"build":[],"run":[]}
    # Compare full operators before timing, not only the prepared state.
    a=builds["sdk"](*args);b=builds["native"](*args)
    if not isinstance(a,tuple):a,b=(a,),(b,)
    for left,right in zip(a,b,strict=True):
        np.testing.assert_allclose(Operator(left.to_qiskit()).data,Operator(right).data,atol=1e-9,rtol=0)
    for i in range(reps):
        observed={}
        for mode in (("sdk","native") if i%2==0 else ("native","sdk")):
            start=time.perf_counter_ns();built=builds[mode](*args);mid=time.perf_counter_ns()
            if family=="syndrome":
                out=built.run().math.statevector() if mode=="sdk" else Statevector.from_instruction(built).data.copy()
                full=out
            else:
                enc,dec=built
                if mode=="sdk":
                    full=dec.run_density(initial_state=enc.run_channel(noise)).data.copy()
                else:
                    full=DensityMatrix.from_instruction(enc).evolve(noise).evolve(dec).data.copy()
                out=sum(full[2*j:2*j+2,2*j:2*j+2] for j in range(4))
            end=time.perf_counter_ns()
            np.testing.assert_allclose(out,expected,atol=1e-9,rtol=0)
            paths[mode]["build"].append((mid-start)/1e6);paths[mode]["run"].append((end-mid)/1e6)
            observed[mode]=full
            if family!="syndrome":paths[mode]["logical_fidelity"]=float(np.vdot(v,out@v).real)
        np.testing.assert_allclose(observed["sdk"],observed["native"],atol=1e-9,rtol=0)
    for row in paths.values():
        for key in ("build","run"):row[key]=stats(row[key])
    return {"family":family,"input":[theta,phi],"noise_or_error":arg,"paths":paths,
            "scope":"coherent syndrome / ideal IID bit-or-phase flip channel; no general fault tolerance or physical noise claim; channel construction excluded equally"}

def run(reps=3):
    return [evaluate(f,t,p,a,reps) for f in ("bit","phase","syndrome") for t,p in ((0.,0.),(.83,-1.17))
            for a in ((None,0,1,2) if f=="syndrome" else (0.,.08,.5,1.))]

if __name__=="__main__":
    print(json.dumps(run(),indent=2,allow_nan=False))
