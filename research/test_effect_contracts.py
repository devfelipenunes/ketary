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
        self.assertEqual(verify_circuit(q.from_qiskit(c),P0,PLUS).status,"PASS")



class GroverComposition(unittest.TestCase):
    """Five wires: four data wires, one clean workspace, two solutions."""

    def test_composed_oracle_and_diffuser(self):
        import ketary as q
        from qiskit.quantum_info import Operator

        eye = np.eye(32, dtype=complex)
        v = eye[:, :16]
        p = v @ v.conj().T
        marked = [i for i in range(16) if ((i & 1) ^ ((i >> 1) & 1))
                  and i & 4 and i & 8]
        self.assertEqual(marked, [13, 14])
        oref = np.diag([-1 if i in marked else 1 for i in range(16)])
        s = np.ones(16) / 4
        dref = 2 * np.outer(s, s) - np.eye(16)

        def oracle(kind):
            c = q.Circuit(5)
            if kind == "direct":
                for i in marked:
                    wires = [w for w in range(4) if not i & (1 << w)]
                    for w in wires:
                        c.x(w)
                    c.h(3).mcx([0, 1, 2], 3).h(3)
                    for w in reversed(wires):
                        c.x(w)
                return c
            if kind == "identity":
                return c
            c.cx(0, 4).cx(1, 4)
            if kind == "wrong_clause":
                c.ccx(2, 4, 3)
            else:
                c.h(3).ccx(2, 4, 3).h(3)
            if kind != "missing_uncompute":
                c.cx(1, 4).cx(0, 4)
            if kind == "phase":
                c.x(0).z(0).x(0).z(0)
            return c

        def diffuser(kind):
            c = q.Circuit(5)
            if kind == "identity":
                return c
            for w in range(4):
                c.h(w).x(w)
            c.h(3).mcx([0, 1, 2], 3).h(3)
            for w in range(4):
                c.x(w).h(w)
            if kind == "wrong":
                c.z(0)
            return c

        def logical_ok(u, ref):
            a = v.conj().T @ u @ v
            inner = np.vdot(ref, a)
            if abs(inner) > 1e-14:
                a = a * np.exp(-1j * np.angle(inner))
            return bool(np.linalg.norm(a-ref, ord=2) <= 1e-9)

        rows = [
            ("good","good",2,(True,True,True,True,True),.9453125),
            ("direct","good",2,(True,True,True,True,True),.9453125),
            ("phase","good",2,(True,True,True,True,True),.9453125),
            ("missing_uncompute","good",2,(False,False,True,True,False),.28125),
            ("wrong_clause","good",2,(True,False,True,True,False),.125),
            ("identity","good",2,(True,False,True,True,False),.125),
            ("good","wrong",2,(True,True,True,False,False),.78125),
            ("good","identity",2,(True,True,True,False,False),.125),
            ("good","good",1,(True,True,True,True,False),.78125),
            ("good","good",3,(True,True,True,True,False),.330078125),
        ]
        for ok, dk, k, expected, prob in rows:
            with self.subTest(oracle=ok, diffuser=dk, iterations=k):
                o, d = oracle(ok), diffuser(dk)
                u, w = Operator(o.to_qiskit()).data, Operator(d.to_qiskit()).data
                # Effect checks, logical restriction checks and algorithm outcome
                # are separate obligations, not inferred from one another.
                a = verify_circuit(o, p, p)
                b = verify_circuit(d, p, p)
                circuit = q.Circuit(5)
                for wire in range(4):
                    circuit.h(wire)
                for _ in range(k):
                    circuit.apply(o).apply(d)
                state = circuit.run().math.statevector()
                success = float(np.sum(np.abs(state[marked]) ** 2))
                got = (a.status == "PASS", logical_ok(u, oref),
                       b.status == "PASS", logical_ok(w, dref),
                       success >= .90)
                self.assertEqual(got, expected)
                self.assertAlmostEqual(success, prob, places=10)
                if not expected[0]:
                    self.assertEqual(a.status, "FAIL")
                    witness = np.array([complex(*part) for part in a.witness])
                    gap = np.vdot(witness, p@witness).real - np.vdot(u@witness, p@(u@witness)).real
                    self.assertAlmostEqual(gap, a.witness_gap)


if __name__=="__main__":
    unittest.main()
