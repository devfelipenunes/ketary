"""Adaptation of QCSE 5959: reset is not coherent uncomputation."""
import ketary as q

def test_reset_destroys_interference():
    def circuit(reset):
        c=q.Circuit.classical(2,2).h(0).cx(0,1)
        if reset:
            c.reset(1)
        else:
            c.cx(0,1)
        return c.h(0).measure(0,0).measure(1,1)
    coherent=circuit(False).run_shots(shots=1024,seed=42)
    reset=circuit(True).run_shots(shots=1024,seed=42)
    assert coherent.counts=={"00":1024}
    assert set(reset.counts)=={"00","01"}
    contract=q.StatisticalContract(2,probabilities={"00":1},margin=.1)
    assert contract.verify(coherent)["status"]=="PASS"
    assert contract.verify(reset)["status"]=="FAIL"
