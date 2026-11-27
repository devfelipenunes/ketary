"""Adversarial and mathematical research tests with real Ketary."""
import unittest
import sys
import random
import subprocess
import json
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Pauli,Statevector
from benchmark import ROOT,label,build,random_g
from round3 import Prepared,prepare,leakage
from engine import Obligation,verify,compose,Native,difference,product_witness,admission
from sparse import propagate
from dataclasses import replace

def circuit(n,gs):
    c=QuantumCircuit(n)
    for op,a,b in gs:
        if op==5:c.cx(a,b)
        else:getattr(c,("h","s","sdg","x","z","cx","t","tdg")[op])(a)
    return q.from_qiskit(c)

def witness_state(w):
    v=np.array([1.],complex)
    for axis,s in reversed(tuple(zip(w.axes,w.signs))):
        a={"X":np.array([1,s])/np.sqrt(2),"Y":np.array([1,1j*s])/np.sqrt(2),"Z":np.array([1,0]) if s==1 else np.array([0,1])}[axis]
        v=np.kron(v,a)
    return v

def native():
    subprocess.run(["g++","-std=c++17","-O3","-shared","-fPIC",str(ROOT/"pauli.cpp"),"-o",str(ROOT/"cpp.so")],check=True)
    subprocess.run(["g++","-std=c++17","-O3","-shared","-fPIC",str(ROOT/"batch.cpp"),"-o",str(ROOT/"batch.so")],check=True)
    return Native()

class Mathematical(unittest.TestCase):
    def test_dense_witnesses(self):
        rng=random.Random(412)
        checks=0
        for n in (1,2,3,4,5):
            for _ in range(32):
                gs=[]
                for j in range(24):
                    op=rng.randrange(8);a=rng.randrange(n)
                    if n==1 and op==5:op=0
                    b=rng.choice([i for i in range(n) if i!=a]) if op==5 else 0
                    gs.append((op,a,b))
                c=circuit(n,gs);p=prepare(c,allow_t=True);u=Operator(c.to_qiskit()).data
                post=(rng.randrange(1<<n),rng.randrange(1<<n),rng.randrange(2))
                expected=u.conj().T@Pauli(label(n,post)).to_matrix()@u
                # Random pre and identity controls; dense independent reference.
                for pre in ((rng.randrange(1<<n),rng.randrange(1<<n),rng.randrange(2)),(0,0,0)):
                    ob=Obligation(pre,post);r=verify(p,(ob,))[0]
                    delta=expected-Pauli(label(n,pre)).to_matrix()
                    ok=np.max(np.abs(delta))<1e-10
                    self.assertEqual(r.status,"PASS" if ok else "FAIL")
                    if not ok:
                        w=r.witness;v=witness_state(w);gap=np.vdot(v,delta@v)
                        a,b=w.numerator;exact=(a+b*np.sqrt(2))/2**w.denominator_power
                        self.assertGreater(abs(exact),1e-10)
                        self.assertAlmostEqual(gap.real,exact,places=10);self.assertAlmostEqual(gap.imag,0.,places=10)
                    checks+=1
        print("DENSE_WITNESS_CHECKS",checks)
    def test_exact_cancellation(self):
        for n in (1,2,16,32,64):
            c=circuit(n,[(6,0,0),(7,0,0)])
            for p in ((1,0,0),(1,1,1),(0,1,1),(0,0,0)):
                self.assertEqual(verify(prepare(c,allow_t=True),(Obligation(p,p),))[0].status,"PASS")
    def test_composition(self):
        x=(1,0,0);z=(0,1,0);negz=(0,1,1)
        h=prepare(circuit(1,[(0,0,0)]))
        local,r=compose(h,h,z,x,z)
        self.assertEqual([v.status for v in local],["PASS","PASS"]);self.assertEqual(r.method,"composition")
        flip=prepare(circuit(1,[(3,0,0)]))
        local,r=compose(flip,flip,z,z,z)
        self.assertEqual([v.status for v in local],["FAIL","FAIL"]);self.assertEqual(r.status,"PASS");self.assertNotEqual(r.method,"composition")
        local,r=compose(flip,h,negz,z,x)
        self.assertEqual(r.status,"PASS")
        rng=random.Random(91)
        for n in (2,3,4):
            for _ in range(24):
                g=random_g(n,10);h2=random_g(n,10)
                a=prepare(circuit(n,g));b=prepare(circuit(n,h2))
                # Independently derive intermediate and initial from Qiskit.
                post=Pauli(label(n,(rng.randrange(1<<n),rng.randrange(1<<n),rng.randrange(2))))
                mid=post.evolve(circuit(n,h2).to_qiskit(),frame="h")
                pre=mid.evolve(circuit(n,g).to_qiskit(),frame="h")
                def bits(p):
                    return sum(int(x)<<i for i,x in enumerate(p.x)),sum(int(z)<<i for i,z in enumerate(p.z)),int(p.phase)//2
                _,r=compose(a,b,bits(pre),bits(mid),bits(post))
                self.assertEqual(r.status,"PASS");self.assertEqual(r.method,"composition")
                u=Operator(circuit(n,g+h2).to_qiskit()).data
                np.testing.assert_allclose(u.conj().T@post.to_matrix()@u,pre.to_matrix(),atol=1e-10)
        print("COMPOSITION_DENSE_CHECKS",72)

class Adversarial(unittest.TestCase):
    def test_admission_budget(self):
        c=circuit(16,[(6,i,0) for i in range(13)]);p=prepare(c,allow_t=True);x=((1<<16)-1,0,0);z=(0,(1<<16)-1,0)
        self.assertEqual(verify(p,(Obligation(x,x),))[0].status,"INCONCLUSIVE")
        self.assertEqual(verify(p,(Obligation(z,z),))[0].status,"PASS")
        self.assertEqual(verify(p,(Obligation(z,z),),method="python")[0].status,"UNSUPPORTED")
        self.assertEqual(verify(p,(Obligation(x,x),Obligation(z,z)),max_terms=4)[1].status,"INCONCLUSIVE")
        self.assertEqual(verify(p,(Obligation(z,z),),max_work=1)[0].status,"INCONCLUSIVE")
        good=prepare(circuit(2,[(0,0,0)]));ob=Obligation((0,1,0),(1,0,0))
        for bad in (replace(good,packed=b"bad"),replace(good,width=0),replace(good,gates=((5,0,0),)),replace(good,gates=((True,0,0),))):
            with self.assertRaises(ValueError):verify(bad,(ob,))
        for bad in (Obligation((True,0,0),(0,0,0)),Obligation((4,0,0),(0,0,0)),Obligation((0,0,2),(0,0,0))):
            with self.assertRaises(ValueError):verify(good,(bad,))
        for kwargs in ({"max_terms":0},{"max_work":True},{"method":"fallback"}):
            with self.assertRaises(ValueError):verify(good,(ob,),**kwargs)
        with self.assertRaises(ValueError):verify(good,(ob,)*65)
        self.assertEqual(verify(good,(ob,),method="scalar")[0].status,"UNSUPPORTED")
        with self.assertRaises(AssertionError):verify(p,(Obligation(x,x),))[0].require()
    def test_identity_and_phase(self):
        c=circuit(2,[(0,0,0)]);p=prepare(c);ob=Obligation((0,1,0),(1,0,0))
        r=verify(p,(ob,))[0];r.require()
        c.z(0);p2=prepare(c);r2=verify(p2,(ob,))[0]
        self.assertNotEqual(r.circuit_id,r2.circuit_id);self.assertEqual(r.status,"PASS");self.assertEqual(r2.status,"FAIL")
        self.assertEqual(verify(p,(ob,))[0],r)
        c2=QuantumCircuit(2);c2.h(0);c2.global_phase=.7
        self.assertEqual(admission(prepare(q.from_qiskit(c2))),r.circuit_id)
    def test_numeric_boundary(self):
        for n in (2,3,5,6):
            for wire in (0,n-1):
                for prob in (0.,.9e-9,1e-9,1.1e-9,.8):
                    c=QuantumCircuit(n);c.ry(2*np.arcsin(np.sqrt(prob)),wire);u=Operator(c).data
                    status,p,w,gap=leakage(u,wire)
                    expected="PASS" if prob<1e-9-1e-12 else "FAIL" if prob>1e-9+1e-12 else "INCONCLUSIVE"
                    self.assertEqual(status,expected);self.assertAlmostEqual(p,prob,places=12)
                    self.assertAlmostEqual(gap,prob,places=12)
        with self.assertRaises(ValueError):leakage(np.eye(4)*.999,0)
        print("LEAKAGE_BOUNDARY_CHECKS",40)

class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.backend=native()
    def test_planner_and_lanes(self):
        rng=random.Random(99);checks=0
        for n in (2,16,32,64):
            for count in (0,1,100,1000):
                p=prepare(circuit(n,random_g(n,count)))
                for m in (1,7,8,32,64):
                    obs=tuple(Obligation((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)),(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))) for _ in range(m))
                    ref=verify(p,obs,method="python")
                    got=verify(p,obs,native=self.backend)
                    self.assertEqual([r.method for r in got],["batch" if m>=8 else "scalar"]*m)
                    self.assertEqual([(r.status,r.witness,r.circuit_id,r.obligation_id) for r in got],[(r.status,r.witness,r.circuit_id,r.obligation_id) for r in ref])
                    checks+=m
        print("NATIVE_REPORT_CHECKS",checks)

if __name__=="__main__":unittest.main()
