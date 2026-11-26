"""Four remaining #293 paired optimization objectives; H2 profiled separately."""
import inspect,json,random,time
import numpy as np
import ketary as q
from scipy.optimize import minimize_scalar
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
from research.circuit_rewrite_ladder import metrics,stats

def problem(kind):
    z=np.diag([1.,-1.]);x=np.array([[0.,1.],[1.,0.]])
    H=.5*(np.kron(z,np.eye(2))+np.kron(np.eye(2),z))+.7*np.kron(x,x)
    ev,vec=np.linalg.eigh(H[np.ix_([0,3],[0,3])])
    ground=np.zeros(4,complex);ground[[0,3]]=vec[:,0]
    target=np.array([np.cos(.73/2),0,0,np.sin(.73/2)],complex)
    bounds,minimum={"spin":((-np.pi,np.pi),ev[0]),"excited":((-np.pi,np.pi),ev[1]),"overlap":((-1.,2.),0.),"multi":((0.,np.pi/2),(1-np.hypot(.4,.7))**2)}[kind]
    return H,ground,target,bounds,float(minimum)

def sdk_path(kind,H,ground,target):
    p=q.Circuit.parameter("theta");n=1 if kind=="multi" else 2
    c=q.Circuit.symbolic(n).ry(p,0)
    if n==2:c.cx(0,1)
    obs=.5*(q.Z(0)+q.Z(1))+.7*(q.X(0)@q.X(1))
    def state(t):return c.bind({p:float(t)}).run()
    def objective(t):
        r=state(t)
        if kind=="multi":return (r.math.expectation(q.X(0))-.4)**2+(r.math.expectation(q.Z(0))-.7)**2
        v=r.math.statevector()
        if kind=="overlap":return 1-abs(np.vdot(target,v))**2
        energy=r.math.expectation(obs)
        return energy+4*abs(np.vdot(ground,v))**2 if kind=="excited" else energy
    return c.to_qiskit(),objective,lambda t:state(t).math.statevector()

def native_path(kind,H,ground,target):
    p=Parameter("theta");n=1 if kind=="multi" else 2
    c=QuantumCircuit(n);c.ry(p,0)
    if n==2:c.cx(0,1)
    def state(t):return Statevector.from_instruction(c.assign_parameters({p:float(t)})).data.copy()
    def objective(t):
        v=state(t)
        if kind=="multi":return (2*np.real(v[0].conj()*v[1])-.4)**2+(abs(v[0])**2-abs(v[1])**2-.7)**2
        if kind=="overlap":return 1-abs(np.vdot(target,v))**2
        energy=float(np.vdot(v,H@v).real)
        return energy+4*abs(np.vdot(ground,v))**2 if kind=="excited" else energy
    return c,objective,state

def reference(kind,t,H,ground,target):
    a,b=np.cos(t/2),np.sin(t/2)
    v=np.array([a,b],complex) if kind=="multi" else np.array([a,0,0,b],complex)
    if kind=="multi":value=(np.sin(t)-.4)**2+(np.cos(t)-.7)**2
    elif kind=="overlap":value=np.sin((t-.73)/2)**2
    else:
        value=np.vdot(v,H@v).real
        if kind=="excited":value+=4*abs(np.vdot(ground,v))**2
    return v,float(value)

def evaluate(kind,seed,reps=3):
    H,g,target,bounds,minimum=problem(kind);rng=random.Random(seed)
    routes={"ketary":sdk_path,"qiskit":native_path};out={}
    angles=[rng.uniform(*bounds) for _ in range(5)]
    for key,fn in routes.items():
        c,obj,state=fn(kind,H,g,target)
        for t in angles:
            v,expected=reference(kind,t,H,g,target)
            np.testing.assert_allclose(state(t),v,atol=1e-9,rtol=0)
            np.testing.assert_allclose(obj(t),expected,atol=1e-9,rtol=0)
        source=inspect.getsource(fn)
        out[key]=dict(source=source,metrics=metrics(source),logical_gates=len(c.data),depth=c.depth(),build=[],optimize=[],histories=[])
    for _ in range(reps):
        for key in rng.sample(list(routes),2):
            t=time.perf_counter_ns();_,obj,_=routes[key](kind,H,g,target);b=time.perf_counter_ns()
            history=[]
            def objective(x):
                val=float(obj(x));history.append([float(x),val]);return val
            result=minimize_scalar(objective,bounds=bounds,method="bounded",options={"xatol":1e-9,"maxiter":100})
            e=time.perf_counter_ns()
            assert result.success and abs(result.fun-minimum)<1e-7
            for angle,value in history:
                np.testing.assert_allclose(value,reference(kind,angle,H,g,target)[1],atol=1e-9,rtol=0)
            out[key]["build"].append((b-t)/1e6);out[key]["optimize"].append((e-b)/1e6)
            out[key]["histories"].append(dict(evaluations=int(result.nfev),parameter=float(result.x),final=float(result.fun),history=history))
    for row in out.values():
        for k in ("build","optimize"):row[k]=stats(row[k])
    return dict(kind=kind,seed=seed,minimum=minimum,paths=out)

def run(reps=3):
    return [evaluate(kind,seed,reps) for seed in (1101,2202,3303) for kind in ("spin","excited","overlap","multi")]

if __name__=="__main__":
    print(json.dumps({"scope":"same bounded optimizer and analytic state/eigenvalue reference; authored shared-CI diagnostic, not general convergence or chemistry claim","rows":run()},indent=2,allow_nan=False))
