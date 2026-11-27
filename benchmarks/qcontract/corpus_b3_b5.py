"""Initial B3–B5 corpus; numeric references do not certify exactness."""
import json,sys,time,statistics
from fractions import Fraction
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli as QPauli,Operator,Statevector,SparsePauliOp
from qcontract import prepare,Pauli,Contract,StateEigen,SumTransition,NoiseAfter,ZBranch,Correctable

def measured(f,reps=5):
    f();samples=[]
    for _ in range(reps):
        t=time.perf_counter_ns();f();samples.append((time.perf_counter_ns()-t)/1e6)
    return {"median_ms":statistics.median(samples),"p95_ms":float(np.percentile(samples,95)),"samples_ms":samples}

def b3():
    from qiskit_aer import AerSimulator
    rows=[];checks=0
    for n in (4,8,16,32,64):
        for tc in (0,4,8,16,32):
            for family in ("ghz-phase","local-graph"):
                c=QuantumCircuit(n)
                if family=="ghz-phase":
                    c.h(0)
                    for j in range(1,n):c.cx(j-1,j)
                else:
                    for j in range(n):c.h(j)
                    for j in range(n-1):
                        c.h(j+1);c.cx(j,j+1);c.h(j+1)
                for j in range(tc):
                    wire=j%n
                    c.t(wire)
                    if family=="local-graph":c.h(wire)
                labels=("I"*(n-1)+"Z","X"*n,"Z"*n,"I"*n)
                specs=tuple(StateEigen(Pauli(x)) for x in labels)
                p=prepare(c)
                def native():return p.verify(*specs)
                results=native()
                saved=c.copy()
                for i,x in enumerate(labels):saved.save_expectation_value(QPauli(x),list(range(n)),label=f"obs{i}")
                sim=AerSimulator(method="matrix_product_state",matrix_product_state_truncation_threshold=0.0,max_parallel_threads=1)
                def mps():
                    result=sim.run(saved,shots=1).result()
                    assert result.success
                    return tuple(float(complex(result.data(0)[f"obs{i}"]).real) for i in range(len(labels)))
                vals=mps()
                for r,v in zip(results,vals):
                    if r.status not in ("PASS","FAIL"):continue
                    (a,b),k=r.expectation
                    exact=(a+b*np.sqrt(2))/2**k
                    assert abs(exact-v)<1e-8,(n,tc,family,exact,v)
                    checks+=1
                assert results[-1].status in ("PASS","INCONCLUSIVE")
                timings={"qcontract_reports_prepared":measured(native),"qcontract_end_to_end":measured(lambda:prepare(c).verify(*specs)),
                         "aer_mps_end_to_end":measured(mps)}
                if n<=16:
                    def dense():
                        s=Statevector.from_instruction(c)
                        return tuple(float(s.expectation_value(QPauli(x)).real) for x in labels)
                    assert np.allclose(dense(),vals,atol=1e-8,rtol=0)
                    timings["dense_end_to_end"]=measured(dense)
                rows.append({"width":n,"t_count":tc,"family":family,"statuses":[r.status for r in results],"values":vals,"timings":timings})
    return {"checks":checks,"rows":rows,"scope":"structured MPS-friendly workloads, float reference and exact coverage; no general MPS or hardware speed claim"}

def b4():
    from mqt import qcec
    rows=[];checks=0
    for n in (4,6,8):
        for family in ("ghz","bv","uncompute"):
            c=QuantumCircuit(n)
            if family=="ghz":
                c.h(0)
                for j in range(1,n):c.cx(0,j)
            elif family=="bv":
                for j in range(n):c.h(j)
                for j in range(0,n,2):c.z(j)
                for j in range(n):c.h(j)
            else:
                for j in range(n-1):c.cx(j,j+1);c.t(j+1)
                for j in reversed(range(n-1)):c.tdg(j+1);c.cx(j,j+1)
            p=prepare(c);a=Operator(c)
            for mode in ("equivalent-rewrite","semantic-mutant"):
                d=c.copy()
                if mode=="equivalent-rewrite":d.s(0);d.sdg(0);d.h(n-1);d.h(n-1)
                else:d.x(n-1)
                want=mode=="equivalent-rewrite"
                assert a.equiv(Operator(d))==want
                ref=prepare(d);spec=p.equivalent_to(ref)
                r=p.check(spec)
                assert r.status in (("PASS" if want else "FAIL"),"INCONCLUSIVE")
                ext=qcec.verify(c,d);verdict=str(ext.equivalence).split(".")[-1]
                if verdict in ("equivalent","equivalent_up_to_global_phase","not_equivalent"):assert (verdict!="not_equivalent")==want
                rows.append({"width":n,"family":family,"mode":mode,"status":r.status,"qcec":verdict,
                             "timings":{"qcontract_prepared":measured(lambda:p.check(spec)),"qcontract_end_to_end":measured(lambda:prepare(c).check(prepare(c).equivalent_to(prepare(d)))),
                                        "qiskit_operator":measured(lambda:Operator(c).equiv(Operator(d))),"qcec_end_to_end":measured(lambda:qcec.verify(c,d))}})
                checks+=1
    return {"checks":checks,"rows":rows,"scope":"initial small complete circuit corpus, known rewrites/mutants; held-out real circuits and complex arithmetic still pending"}

def b5():
    rows=[];checks=0
    c=QuantumCircuit(2);c.h(0);p=prepare(c);u=Operator(c).data
    for denominator in (2,3,5,7,11):
        f=Fraction(1,denominator);z=Pauli("IZ");x=Pauli("IX")
        a=SparsePauliOp.from_list([("IZ",float(f)),("II",0.5)]).to_matrix()
        b=SparsePauliOp.from_list([("IX",float(f)),("II",0.5)]).to_matrix()
        assert np.allclose(u.conj().T@b@u,a,atol=1e-12,rtol=0)
        spec=SumTransition(((z,f),(Pauli("II"),Fraction(1,2))),((x,f),(Pauli("II"),Fraction(1,2))))
        mutant=SumTransition(((z,-f),(Pauli("II"),Fraction(1,2))),spec.post)
        assert [r.status for r in p.verify(spec,mutant)]==["PASS","FAIL"];checks+=2
        rows.append({"family":"sum","denominator":denominator,"timings":measured(lambda:p.verify(spec,mutant))})
    for weight in range(5):
        pre,post=Pauli("IZ"),Pauli("IX");identity=Pauli("II")
        entries=tuple((e,w) for e,w in ((identity,4-weight),(pre,weight)) if w)
        factor=Fraction(4-2*weight,4)
        op=QPauli("IX").to_matrix();err=QPauli("IZ").to_matrix()
        got=u.conj().T@((4-weight)*op+weight*err@op@err)/4@u
        assert np.allclose(got,float(factor)*QPauli("IZ").to_matrix(),atol=1e-12,rtol=0)
        spec=NoiseAfter(pre,post,entries,4,factor)
        assert p.check(spec).status=="PASS";checks+=1
        rows.append({"family":"noise","weight":weight,"timings":measured(lambda:p.check(spec))})
    for entangled in (False,True):
        b=QuantumCircuit(2)
        if entangled:b.h(0);b.cx(0,1)
        p=prepare(b);psi=Statevector.from_instruction(b).data
        for outcome in (0,1):
            prob=Fraction(1,2) if entangled else Fraction(int(outcome==0))
            ev=prob*(-1)**outcome
            def dyadic(f):return ((f.numerator,0),f.denominator.bit_length()-1)
            branch=psi.copy()
            for j in range(len(branch)):
                if j%2!=outcome:branch[j]=0
            assert abs(np.vdot(branch,branch).real-float(prob))<1e-10
            assert abs(np.vdot(branch,QPauli("IZ").to_matrix()@branch).real-float(ev))<1e-10
            spec=ZBranch(0,outcome,Pauli("IZ"),dyadic(prob),dyadic(ev))
            assert p.check(spec).status=="PASS";checks+=1
            rows.append({"family":"z-branch","entangled":entangled,"outcome":outcome,"timings":measured(lambda:p.check(spec))})
    p=prepare(QuantumCircuit(3));st=tuple(Pauli(x) for x in ("IZZ","ZZI"))
    proj=(np.eye(8)+QPauli("IZZ").to_matrix())@(np.eye(8)+QPauli("ZZI").to_matrix())/4
    for labels in (("III","IIX","IXI","XII"),("III","IIX","IXI","XII","XXX")):
        es=tuple(QPauli(x).to_matrix() for x in labels);ok=True
        for e in es:
            for f in es:
                t=proj@e.conj().T@f@proj
                ok &= bool(np.allclose(t,np.trace(t)/np.trace(proj)*proj,atol=1e-12,rtol=0))
        spec=Correctable(st,tuple(Pauli(x) for x in labels))
        assert p.check(spec).status==("PASS" if ok else "FAIL");checks+=1
        rows.append({"family":"qec","errors":len(labels),"timings":measured(lambda:p.check(spec))})
    return {"checks":checks,"rows":rows,"scope":"finite exact domains and independent numerical matrix controls, no general noise or fault tolerance"}

if __name__=="__main__":
    suite=sys.argv[1];print(json.dumps({"suite":suite,**{"b3":b3,"b4":b4,"b5":b5}[suite]()},indent=2,allow_nan=False))
