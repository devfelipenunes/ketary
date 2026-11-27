"""Oracle checks are independent of external SDK installations."""
import unittest
import numpy as np
from competitive_sdk import reference, workload, check, measure, FAMILIES, ROUTES


class OracleTests(unittest.TestCase):
    def test_bell(self):
        np.testing.assert_allclose(reference(2,[("h",(0,)),("cx",(0,1))]),
                                   [2**-.5,0,0,2**-.5],atol=1e-12)
    def test_order_and_phase(self):
        np.testing.assert_allclose(reference(3,[("x",(0,)),("swap",(0,2)),("rz",(np.pi,2))]),
                                   [0,0,0,0,1j,0,0,0],atol=1e-12)
        v=reference(2,[("x",(0,)),("x",(1,)),("cp",(np.pi/2,0,1))])
        np.testing.assert_allclose(v,[0,0,0,1j],atol=1e-12)
    def test_qft_known_input(self):
        for n in (3,4):
            expected=np.exp(2j*np.pi*np.arange(1<<n)/(1<<n))/np.sqrt(1<<n)
            np.testing.assert_allclose(reference(n,workload("qft",n,7)),expected,atol=1e-12)
    def test_reject_phase_dtype_and_mutation(self):
        v=reference(2,workload("ghz",2,1))
        for actual in (-v,v.astype(np.complex64),v[::-1].copy()+.1):
            with self.assertRaises(AssertionError):
                check(actual,v)


class CrossSdkTests(unittest.TestCase):
    def test_all_families(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                row=measure(family,3,7,3)
                self.assertEqual(set(row["semantic"]),set(ROUTES))
                for stage in row["stages"].values():
                    self.assertEqual(len(stage["order"]),3)
                    self.assertTrue(all(len(v["raw_ms"])==3 for v in stage["samples"].values()))


if __name__=="__main__":
    unittest.main()
