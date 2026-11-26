"""Two authored optimization applications with explicit objectives and gradients.

No installed API, hardware or claim of global variational optimality.
Use fixed bounded problems, identical starting points and optimizer budgets.
Independent dense evolution plus native Qiskit direct gates verify objectives.
"""
import argparse,json,time
from pathlib import Path
import numpy as np
import ketary as q
from scipy.linalg import expm
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector,SparsePauliOp
from research.occurrence_gradient import jacobian
from research.workflow_depth import dense,label

def problem(kind):
    if kind=="maxcut":
        n=3;edges=[(0,1),(1,2),(0,2)];weights=[.7,1.1,.9]
        H=q.maxcut_hamiltonian(n,edges,weights=weights)
        M=sum(q.X(i) for i in range(n))
        g,b=q.Circuit.parameter_vector("p",2)
        c=q.Circuit.symbolic(n).h(range(n)).evolve(H,time=g).evolve(M,time=b)
        costs=np.array([sum(w*(((i>>a)^(i>>b))&1) for (a,b),w in zip(edges,weights,strict=True)) for i in range(8)])
        h=np.diag(costs);m=dense(M.to_dict(n))
        def oracle(x):return expm(-1j*x[1]*m)@(np.exp(-1j*x[0]*costs)/np.sqrt(8))
        def native(x):
            raw=QuantumCircuit(n);raw.h(range(n));raw.global_phase-=sum(weights)*x[0]/2
            for (a,b),w in zip(edges,weights,strict=True):raw.rzz(-w*x[0],a,b)
            raw.rx(2*x[1],range(n))
            return Statevector.from_instruction(raw).data
        sign=-1.;optimum=float(max(costs))
    elif kind=="spin_vqe":
        n=2;terms={"ZI":-.7,"IZ":-.4,"XX":.6,"ZZ":.2,"II":.1}
        H=q.Observable(terms);h=dense(terms)
        p=q.Circuit.parameter_vector("p",4)
        c=q.Circuit.symbolic(n).ry(p[:2],range(n)).cx(0,1).ry(p[2:],range(n))
        def oracle(x):
            def ry(t):return np.array([[np.cos(t/2),-np.sin(t/2)],[np.sin(t/2),np.cos(t/2)]])
            initial=np.kron(ry(x[1]),ry(x[0]))[:,0]
            perm=[i^((i&1)<<1) for i in range(4)]
            return np.kron(ry(x[3]),ry(x[2]))@initial[perm]
        def native(x):
            raw=QuantumCircuit(n);raw.ry(x[0],0);raw.ry(x[1],1);raw.cx(0,1)
            raw.ry(x[2],0);raw.ry(x[3],1)
            return Statevector.from_instruction(raw).data
        sign=1.;optimum=float(np.linalg.eigvalsh(h)[0])
    else:raise ValueError("unknown application")
    return c,H,h,oracle,native,sign,optimum

def evaluate(kind,seed=1101):
    c,H,h,oracle,native,sign,optimum=problem(kind)
    rng=np.random.default_rng(seed)
    x0=rng.uniform(-.6,.6,len(c.parameters))
    if kind=="maxcut":x0=np.array([.4,.3])+rng.uniform(-.05,.05,2)
    def objective(v):return float(np.vdot(v,h@v).real)
    def oracle_cost(x):return sign*objective(oracle(x))
    def native_cost(x):return sign*objective(native(x))
    def ketary_cost(x):return sign*c.bind(x).run().math.expectation(H)
    def grad(x):
        bindings=dict(zip(c.parameters,x,strict=True))
        return sign*jacobian(c,bindings,[H])["jacobian"][0]
    max_error=0.
    for x in (x0,rng.uniform(-1,1,len(x0))):
        ref=oracle(x)
        for state in (native(x),c.bind(x).run().math.statevector()):
            max_error=max(max_error,float(np.max(np.abs(state-ref))))
        eps=1e-5;eye=np.eye(len(x))
        fd=np.array([(oracle_cost(x+eps*i)-oracle_cost(x-eps*i))/(2*eps) for i in eye])
        np.testing.assert_allclose(grad(x),fd,atol=1e-8,rtol=0)
    outputs={}
    for name,fn,j in (("ketary",ketary_cost,grad),("qiskit",native_cost,None)):
        history=[float(fn(x0))]
        t=time.perf_counter_ns()
        result=minimize(fn,x0,jac=j,method="BFGS",callback=lambda x:history.append(float(fn(x))),
                        options={"maxiter":40,"gtol":1e-7})
        elapsed=(time.perf_counter_ns()-t)/1e6
        value=float(fn(result.x));exact=oracle_cost(result.x)
        max_error=max(max_error,abs(value-exact))
        assert value<=history[0]+1e-8
        assert value>=sign*optimum-1e-8
        outputs[name]=dict(initial=sign*history[0],final=sign*value,parameters=result.x.tolist(),
                           history=[sign*x for x in history],iterations=int(result.nit),
                           optimizer_success=bool(result.success),message=str(result.message),nfev=int(result.nfev),
                           njev=int(result.njev),elapsed_ms=elapsed)
    assert max_error<1e-9
    return dict(kind=kind,seed=seed,reference_optimum=optimum,max_error=max_error,variants=outputs,
                scope="authored small variational problem; optimizer comparison different derivative methods, not fair performance baseline or global convergence guarantee")
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[evaluate(k,a.seed) for k in ("maxcut","spin_vqe")]
    for row in rows:print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(rows,indent=2,allow_nan=False))
if __name__=="__main__":main()
