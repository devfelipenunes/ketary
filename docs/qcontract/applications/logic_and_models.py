"""Application checks for coherent logic, compilation and model auditing."""
from fractions import Fraction

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli as MP
from qcontract import (Named, NoiseAfter, Pauli, Plan, SumTransition,
                       clean_ancillas, prepare, transition)


def vector_status(outcome):
    return tuple(r.status for _,r in outcome.results)


def swap(c,a,b):
    c.cx(a,b);c.cx(b,a);c.cx(a,b)


def cz(c,a,b):
    c.h(b);c.cx(a,b);c.h(b)


def teleportation():
    """Coherent state transfer with workspace reset, not a network protocol."""
    ref_c=QuantumCircuit(3)
    swap(ref_c,0,2)
    ref=prepare(ref_c)
    # Independent linear map from logical input wire 0 to output wire 2.
    target=np.zeros((8,2),complex);target[0,0]=target[4,1]=1
    rows=[]
    for case,expected in (("complete","PASS"),("missing phase correction","FAIL"),
                          ("missing bit correction","FAIL"),("unclean record","FAIL")):
        c=QuantumCircuit(3)
        c.h(1);c.cx(1,2)
        c.cx(0,1);c.h(0)
        if case!="missing bit correction":
            c.cx(1,2)
        if case!="missing phase correction":
            cz(c,0,2)
        if case!="unclean record":
            c.h(0);c.h(1)
        p=prepare(c)
        plan=Plan((Named("Transfer arbitrary logical input",
                         p.action_matches(ref,ancillas=(1,2))),))
        outcome=plan.verify(p)
        actual=Operator(c).data[:,:2]
        phase=actual[0,0]
        numeric="PASS" if np.isclose(abs(phase),1,rtol=0,atol=1e-12) and np.allclose(
            actual,phase*target,rtol=0,atol=1e-12) else "FAIL"
        assert vector_status(outcome)==(expected,)==(numeric,), (case,vector_status(outcome),numeric)
        rows.append({"case":case,"numeric":numeric,"reports":outcome.explain()})
    return {"cases":rows,"purpose":"coherent state transfer on clean-input subspace"}


def parity_workspace():
    """Compute parity in a workspace, use it for phase, then uncompute."""
    ref_c=QuantumCircuit(3)
    ref_c.z(0);ref_c.z(1)
    ref=prepare(ref_c)
    target=np.diag([1,-1,-1,1])
    rows=[]
    for case,expected in (("complete",("PASS","PASS")),("missing uncompute",("FAIL","FAIL")),
                          ("missing phase",("PASS","FAIL")),("extra workspace Z",("PASS","PASS"))):
        c=QuantumCircuit(3)
        c.cx(0,2);c.cx(1,2)
        if case!="missing phase":
            c.z(2)
        if case!="missing uncompute":
            c.cx(1,2);c.cx(0,2)
        if case=="extra workspace Z":
            c.z(2)
        p=prepare(c)
        plan=Plan((clean_ancillas("Restore parity workspace",wires=(2,)),
                   Named("Apply logical parity phase",p.action_matches(ref,ancillas=(2,)))))
        outcome=plan.verify(p)
        m=Operator(c).data[:,:4]
        clean=np.allclose(m[4:,:],0,rtol=0,atol=1e-12)
        phase=m[0,0]
        action=clean and np.isclose(abs(phase),1,rtol=0,atol=1e-12) and np.allclose(
            m[:4,:],phase*target,rtol=0,atol=1e-12)
        numeric=tuple("PASS" if x else "FAIL" for x in (clean,action))
        assert vector_status(outcome)==expected==numeric
        rows.append({"case":case,"numeric":numeric,"reports":outcome.explain()})
    return {"cases":rows,"purpose":"audit reversible parity phase and workspace"}


def compiler_rewrite():
    """Accept exact T-pair reduction; distinguish a phase-only rewrite."""
    c=QuantumCircuit(1);c.h(0);c.t(0);c.t(0);c.h(0)
    ref=prepare(c);reference=Operator(c).data
    rows=[]
    for name,gates,expected in (
        ("S reduction",("h","s","h"),("PASS","PASS")),
        ("global minus",("h","s","h","x","z","x","z"),("PASS","FAIL")),
        ("lost T",("h","t","h"),("FAIL","FAIL")),
    ):
        candidate=QuantumCircuit(1)
        for gate in gates:
            getattr(candidate,gate)(0)
        p=prepare(candidate)
        plan=Plan((Named("Equivalent modulo common phase",p.equivalent_to(ref)),
                   Named("Strict equivalence",p.equivalent_to(ref,strict=True))))
        outcome=plan.verify(p)
        u=Operator(candidate).data
        overlap=np.trace(reference.conj().T@u)/2
        numeric=("PASS" if np.allclose(u,overlap*reference,rtol=0,atol=1e-12) and np.isclose(
                    abs(overlap),1,rtol=0,atol=1e-12) else "FAIL",
                 "PASS" if np.allclose(u,reference,rtol=0,atol=1e-12) else "FAIL")
        assert vector_status(outcome)==expected==numeric
        rows.append({"case":name,"numeric":numeric,"reports":outcome.explain()})
    return {"cases":rows,"purpose":"validate a bounded compiler rewrite"}


def hamiltonian_mapping():
    """Map rational Pauli coefficients under a wire permutation."""
    pre=(("IZ",Fraction(1,3)),("ZI",Fraction(2,3)),("XX",Fraction(1,2)))
    post=(("ZI",Fraction(1,3)),("IZ",Fraction(2,3)),("XX",Fraction(1,2)))
    spec=SumTransition(tuple((Pauli(p),w) for p,w in pre),
                       tuple((Pauli(p),w) for p,w in post))
    plan=Plan((Named("Map weighted Hamiltonian",spec),))
    a=sum(float(w)*MP(p).to_matrix() for p,w in pre)
    b=sum(float(w)*MP(p).to_matrix() for p,w in post)
    rows=[]
    for case,expected in (("swap","PASS"),("swap plus identity","PASS"),
                          ("identity","FAIL"),("partial swap","FAIL")):
        c=QuantumCircuit(2)
        if case in ("swap","swap plus identity"):
            swap(c,0,1)
        if case=="swap plus identity":
            c.cx(0,1);c.cx(0,1)
        if case=="partial swap":
            c.cx(0,1);c.cx(1,0)
        outcome=plan.verify(prepare(c))
        u=Operator(c).data
        numeric="PASS" if np.allclose(u.conj().T@b@u,a,rtol=0,atol=1e-12) else "FAIL"
        assert vector_status(outcome)==(expected,)==(numeric,)
        rows.append({"case":case,"numeric":numeric,"reports":outcome.explain()})
    return {"cases":rows,"purpose":"audit ideal weighted-observable remapping, not VQE"}


def noise_transfer():
    """Check a specified finite Pauli channel's observable attenuation."""
    rows=[]
    for phase_weight in (0,1,2,3,4):
        entries=tuple((Pauli(p),w) for p,w in (("I",4-phase_weight),("Z",phase_weight)) if w)
        coefficient=Fraction(4-2*phase_weight,4)
        for wrong in (False,True):
            # Deliberately wrong, distinct admitted target coefficient.
            claimed=coefficient if not wrong else (Fraction(0) if coefficient else Fraction(1))
            c=QuantumCircuit(1);c.h(0)
            p=prepare(c)
            spec=NoiseAfter(Pauli("Z"),Pauli("X"),entries,4,claimed)
            outcome=Plan((Named("Noisy transfer coefficient",spec),)).verify(p)
            u=Operator(c).data
            x,z=MP("X").to_matrix(),MP("Z").to_matrix()
            observed=u.conj().T@((4-phase_weight)*x+phase_weight*(z@x@z))@u/4
            numeric="PASS" if np.allclose(observed,float(claimed)*z,rtol=0,atol=1e-12) else "FAIL"
            expected="FAIL" if wrong else "PASS"
            assert vector_status(outcome)==(expected,)==(numeric,), (phase_weight,wrong,vector_status(outcome))
            rows.append({"phase_weight":phase_weight,"denominator":4,
                         "claimed":str(claimed),"numeric":numeric,"reports":outcome.explain()})
    return {"cases":rows,"purpose":"validate declared Pauli-channel model, not device calibration"}
