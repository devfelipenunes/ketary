"""Round 9: matched compiled Python/Rust contract verification and native witnesses."""
from common5 import *
from native9 import RustSession,TransitionContract
from front_rust8 import compile_native,outcome
from fast_sparse7 import propagate_fast
from sparse import propagate,BudgetExceeded
from engine import product_witness,difference,verify
from test_engine import witness_state
from qiskit.quantum_info import Operator,Pauli
from qiskit import QuantumCircuit
from concurrent.futures import ThreadPoolExecutor
import ketary as q
from dataclasses import asdict
from importlib.metadata import version
def proj(rs):return [(r.status,r.obligation_id,r.scope,r.witness) for r in rs]
def main():
    ffi=compile_native();rng=random.Random(987);checks=limits=0;rows=[]
    for n in (1,2,3,4,5):
        for j in range(48):
            gs=[]
            for k in range(32):
                op=rng.randrange(8);a=rng.randrange(n)
                if n==1 and op==5:op=0
                b=rng.choice([i for i in range(n) if i!=a]) if op==5 else 0
                gs.append((op,a,b))
            c=circuit(n,gs);p=prepare(c,allow_t=True);s=RustSession.from_circuit(c)
            assert s.packed==p.packed
            post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            r=s.propagate(post);assert r==propagate(n,p.gates,post)==ffi.run(p,post)
            u=Operator(c.to_qiskit()).data
            target=u.conj().T@Pauli(label(n,post)).to_matrix()@u
            reconstructed=sum(((a+b*np.sqrt(2))/(1<<r.denominator_power)*Pauli(label(n,(x,z,0))).to_matrix() for x,z,a,b in r.terms),np.zeros_like(u))
            np.testing.assert_allclose(target,reconstructed,atol=1e-10)
            for pre in (post,(0,0,0),(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))):
                ob=Obligation(pre,post);got=s.verify((ob,));ref=verify(p,(ob,),method="sparse")
                assert proj(got)==proj(ref),(n,j,pre,post,got,ref)
                delta=target-Pauli(label(n,pre)).to_matrix()
                assert got[0].status==("PASS" if np.max(np.abs(delta))<1e-10 else "FAIL")
                if got[0].witness:
                    w=got[0].witness;v=witness_state(w);a,b=w.numerator
                    assert abs(np.vdot(v,delta@v).real-(a+b*np.sqrt(2))/(1<<w.denominator_power))<1e-10
                checks+=1
            for kw in ({"max_terms":1},{"max_terms":4},{"max_work":1},{"max_work":32}):
                assert outcome(lambda:s.propagate(post,**kw))==outcome(lambda:propagate(n,p.gates,post,**kw));limits+=1
    for n in (16,32,64):
        for t in (4,8,12):
            c=circuit(n,[(4,i%n,0) for i in range(100)]+[(6,i,0) for i in range(t)])
            p=prepare(c,allow_t=True);s=RustSession.from_circuit(c)
            for kind in ("commuting","branching"):
                post=((1<<n)-1,0,0) if kind=="branching" else (0,(1<<n)-1,0)
                ob=Obligation(post,post);obs=(ob,)
                def reference():return verify(p,obs,method="sparse")
                def full_ref():return verify(prepare(c,allow_t=True),obs,method="sparse")
                def full_native():return RustSession.from_circuit(c).verify(obs)
                def ffi_report():
                    r=ffi.run(p,post);d=difference(r.terms,r.denominator_power,post)
                    return ("FAIL" if d else "PASS",product_witness(n,d,r.denominator_power) if d else None)
                got=s.verify(obs);assert proj(got)==proj(reference())==proj(full_native())
                assert ffi_report()==(got[0].status,got[0].witness)
                rows.append({"n":n,"T":t,"kind":kind,"status":got[0].status,"timings":measure({"python_full_report":full_ref,"python_prepared_report":reference,"ffi_kernel_plus_witness":ffi_report,"pyo3_full_report":full_native,"pyo3_session_report":lambda:s.verify(obs),"pyo3_terms":lambda:s.propagate(post)},reps=7)})
    # Actual Ketary circuits and contract usage; scope is transition, not snapshot.
    algo=[]
    for n in (4,16,32,64):
        for bad in (False,True):
            c=q.ghz(n) if n<=16 else circuit(n,[(0,0,0)]+[(5,0,i) for i in range(1,n)])
            if bad:c.z(0)
            contract=TransitionContract((0,1,0),((1<<n)-1,0,0))
            status=contract.verify(c).status
            assert status==("FAIL" if bad else "PASS")
            if n==4:
                # Existing public snapshot contract remains a distinct API.
                assert q.Contract(n,expectations={"X"*n:-1. if bad else 1.}).verify(c.run()).status=="PASS"
            algo.append({"n":n,"mutant":bad,"status":status})
    c=circuit(64,[(6,1+i%63,0) for i in range(10000)]+[(0,0,0)])
    s=RustSession.from_circuit(c);ob=Obligation((0,1,0),(1,0,0))
    assert s.verify((ob,))[0].status=="INCONCLUSIVE"
    assert s.verify((ob,),adaptive=True)[0].status=="PASS"
    c.z(0);assert RustSession.from_circuit(c).identity!=s.identity
    # Native object can be shared for explicit independent calls; no mutable Circuit shared.
    c=circuit(32,[(4,i%32,0) for i in range(100)]+[(6,i,0) for i in range(10)])
    s=RustSession.from_circuit(c);p=((1<<32)-1,0,0);obs=(Obligation(p,p),)
    baseline=s.verify(obs)
    threads=[]
    for workers in (1,2,4):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            def par():return list(pool.map(lambda _:s.verify(obs),range(8)))
            assert par()==[baseline]*8
            threads.append({"workers":workers,"timings":measure({"serial":lambda:[s.verify(obs) for _ in range(8)],"pool":par},reps=7)})
    output({"scope":"exact Pauli transition, native witnesses and matched reports; circuit identity v3 differs intentionally; FFI kernel+witness excludes report; shared CI; no runtime change","pyo3_package":version("ketary-native-research"),"dense_contract_checks":checks,"budget_checks":limits,"rows":rows,"algorithms":algo,"thread_rows":threads})
if __name__=="__main__":main()
