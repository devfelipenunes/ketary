"""Bounded #154/#303 comparison: coherent parity and symbolic local-basis reuse."""
import argparse,inspect,json,os,random,resource,subprocess,sys,time
import numpy as np
import ketary as q
from scipy.linalg import expm
from qiskit import QuantumCircuit,transpile
from qiskit.quantum_info import Operator,Statevector
from research.alpha_mixed_parity import shared,native,fixture
from research.circuit_rewrite_ladder import metrics,stats

def dense(terms):
    matrices={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    result=0
    for label,w in terms.items():
        m=np.ones((1,1),complex)
        for a in label:m=np.kron(m,matrices[a])
        result=result+w*m
    return result

def symbolic_shared(n,terms,p):
    axes={};diagonal={}
    for label,w in terms.items():
        for wire,axis in enumerate(reversed(label)):
            if axis=="I":continue
            if wire in axes and axes[wire]!=axis:raise ValueError("common local basis required")
            axes[wire]=axis
        diagonal["".join("I" if a=="I" else "Z" for a in label)]=w
    c=q.Circuit.symbolic(n)
    for wire,axis in sorted(axes.items()):
        if axis=="X":c.h(wire)
        elif axis=="Y":c.sdg(wire).h(wire)
    c.evolve(q.Observable(diagonal),time=p)
    for wire,axis in reversed(sorted(axes.items())):
        if axis=="X":c.h(wire)
        elif axis=="Y":c.h(wire).s(wire)
    return c

def sdk_bound(n,terms,t):
    return q.Circuit(n).evolve(q.Observable(terms),time=t).to_qiskit()

def sdk_shared(n,terms,t):
    return shared(n,terms,t).to_qiskit()

def sdk_symbolic(n,terms,t):
    p=q.Circuit.parameter("t")
    return symbolic_shared(n,terms,p).bind({p:t}).to_qiskit()

def coherent():
    c=q.Circuit(4).cx(pairs=[(2,1),(0,1)])
    raw=QuantumCircuit(4);raw.cx(2,1);raw.cx(0,1)
    expected=np.zeros((16,16),complex)
    for j in range(16):expected[j^((((j>>2)^j)&1)<<1),j]=1
    for obj in (c.to_qiskit(),raw):
        np.testing.assert_allclose(Operator(obj).data,expected,atol=1e-9,rtol=0)
    # Clean and occupied target included in all columns, spectator wire 3.
    v=np.arange(1,17)+1j*np.arange(16,0,-1);v=v/np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),expected@v,atol=1e-9,rtol=0)
    bell=q.Circuit(2).h(0).cx(0,1).run()
    rho=bell.math.density_matrix([0,1]);dephased=np.diag(np.diag(rho))
    assert abs(rho[0,3])>.49 and dephased[0,3]==0
    return {"coherent_off_diagonal":float(rho[0,3].real),"nonselective_measured_off_diagonal":float(dephased[0,3].real)}

def worker(n,seed,route,reps):
    terms=fixture(n,seed);t=.37 if seed!=2202 else -.41
    expected=expm(-1j*t*dense(terms));rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    routes={"bound":(sdk_bound,()),"shared":(sdk_shared,(shared,)),"symbolic":(sdk_symbolic,(symbolic_shared,)),"native":(native,())}
    fn,helpers=routes[route];before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    build=[];run=[]
    for _ in range(reps):
        a=time.perf_counter_ns();raw=fn(n,terms,t);b=time.perf_counter_ns()
        out=Statevector(v).evolve(raw).data.copy();e=time.perf_counter_ns()
        np.testing.assert_allclose(out,expected@v,atol=1e-9,rtol=0)
        build.append((b-a)/1e6);run.append((e-b)/1e6)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    low=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
    for c in (raw,low):np.testing.assert_allclose(Operator(c).data,expected,atol=1e-9,rtol=0)
    source="\n\n".join(inspect.getsource(f) for f in (fn,*helpers))
    return dict(n=n,seed=seed,route=route,terms=len(terms),source=source,metrics=metrics(source),build=stats(build),run=stats(run),logical_gates=len(raw.data),common_gates=len(low.data),common_cx=int(low.count_ops().get("cx",0)),common_depth=low.depth(),baseline_hwm_kib=before,post_work_hwm_kib=peak,payload_bytes=out.nbytes)

def study(reps):
    if not sys.platform.startswith("linux"):raise RuntimeError("Linux RSS units")
    rng=random.Random(1101);rows=[]
    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
    for seed in (1101,2202,3303):
        for n in (4,5,6):
            for route in rng.sample(["bound","shared","symbolic","native"],4):
                data=subprocess.check_output([sys.executable,"-m","research.alpha_four_parity","--worker",str(n),str(seed),route,"--reps",str(reps)],env=env,text=True,timeout=120)
                rows.append(json.loads(data))
    return dict(scope="strict matched operators; native high-level build vs explicit lowering; isolated Linux process HWM includes imports/oracle, not incremental allocation or total physical memory; common-basis lowering after measured stages",coherent=coherent(),rows=rows)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--worker",nargs=3);p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if not 1<=a.reps<=20:p.error("reps 1..20")
    print(json.dumps(worker(int(a.worker[0]),int(a.worker[1]),a.worker[2],a.reps) if a.worker else study(a.reps),indent=2,allow_nan=False))
