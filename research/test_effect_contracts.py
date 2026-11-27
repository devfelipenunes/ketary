"""Independent analytic controls and actual public SDK integration."""
import unittest
import numpy as np
from effect_contracts import verify_effect,verify_circuit,verify_sequence,projector,demo

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Z=np.diag([1,-1]).astype(complex)
H=np.array([[1,1],[1,-1]],complex)/np.sqrt(2)
P0=projector(np.array([1,0]))
P1=projector(np.array([0,1]))
PLUS=projector(np.array([1,1])/np.sqrt(2))


class Effects(unittest.TestCase):
    def test_unitary_and_witness(self):
        self.assertEqual(verify_effect(P0,PLUS,(H,)).status,"PASS")
        bad=verify_effect(P0,PLUS,(Z@H,))
        self.assertEqual(bad.status,"FAIL")
        w=np.array([complex(*p) for p in bad.witness])
        self.assertAlmostEqual(np.vdot(w,w).real,1)
        self.assertAlmostEqual(bad.witness_gap,1)
        self.assertAlmostEqual(np.vdot(w,P0@w).real-np.vdot(Z@H@w,PLUS@(Z@H@w)).real,1)

    def test_amplitude_damping(self):
        g=.3
        k=(np.diag([1,np.sqrt(1-g)]),np.array([[0,np.sqrt(g)],[0,0]]))
        self.assertEqual(verify_effect(P0,P0,k).status,"PASS")
        self.assertAlmostEqual(verify_effect(P1,P1,k).max_residual,g)
        self.assertEqual(verify_effect(P1,P1,k).status,"FAIL")

    def test_sequence(self):
        r=verify_sequence(P0,PLUS,P1,(H,),(X@H,))
        self.assertEqual([r[k]["status"] for k in ("first","second","direct")],["PASS"]*3)
        bad=verify_sequence(P0,PLUS,P0,(H,),(X@H,))
        self.assertEqual(bad["second"]["status"],"FAIL")
        self.assertEqual(bad["direct"]["status"],"FAIL")

    def test_context_and_domain(self):
        self.assertEqual(verify_effect(P0,P0,(I,)).status,"PASS")
        self.assertEqual(verify_effect(P0,P0,(Z,)).status,"PASS")
        self.assertEqual(verify_effect(PLUS,PLUS,(Z,)).status,"FAIL")
        self.assertEqual(verify_effect(PLUS,PLUS,(-I,)).status,"PASS")

    def test_boundary(self):
        self.assertEqual(verify_effect(P0,P0,(I,),atol=0).status,"INCONCLUSIVE")
        for bad in (True,-1,float("nan"),1e-3):
            with self.assertRaises(ValueError): verify_effect(P0,P0,(I,),atol=bad)
        for bad in (2*I,np.array([[0,1],[0,0]]),np.full((2,2),np.nan),np.eye(64)):
            with self.assertRaises(ValueError): verify_effect(bad,P0,(I,))
        for bad in ((I/2,),(),(I,)*17):
            with self.assertRaises(ValueError): verify_effect(P0,P0,bad)
        with self.assertRaises(ValueError): verify_sequence(P0,P0,P0,(I/np.sqrt(5),)*5,(I/2,)*4)

    def test_provenance_and_ownership(self):
        a=P0.copy()
        r=verify_effect(a,P0,(I,))
        a[:]=0
        self.assertEqual(r.status,"PASS")
        self.assertNotEqual(r.specification_sha256,verify_effect(a,P0,(I,)).specification_sha256)
        self.assertNotEqual(r.channel_sha256,verify_effect(P0,P0,(Z,)).channel_sha256)
        self.assertEqual(r.to_dict(),verify_effect(P0,P0,(I,)).to_dict())


class KetaryIntegration(unittest.TestCase):
    def test_bell(self):
        r=demo()
        self.assertEqual(r["bell"]["snapshot"]["status"],"PASS")
        self.assertEqual(r["bell"]["effect"]["status"],"PASS")
        self.assertEqual(r["relative_phase_mutant"]["snapshot"]["status"],"FAIL")
        self.assertEqual(r["relative_phase_mutant"]["effect"]["status"],"FAIL")

    def test_reject_symbolic_and_width(self):
        import ketary as q
        with self.assertRaises(ValueError): verify_circuit(q.Circuit(6),P0,P0)
        p=q.Circuit.parameter("t")
        with self.assertRaises(ValueError): verify_circuit(q.Circuit.symbolic(1).ry(p,0),P0,P0)

    def test_native_interop(self):
        import ketary as q
        from qiskit import QuantumCircuit
        c=QuantumCircuit(1)
        c.h(0)
        self.assertEqual(verify_circuit(q.Circuit.from_qiskit(c),P0,PLUS).status,"PASS")


if __name__=="__main__":
    unittest.main()
