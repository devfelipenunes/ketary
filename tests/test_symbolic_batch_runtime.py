"""Public symbolic gate transaction, not generic composition rollback."""
import pytest
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("kind",["h","ry","rzz","cx"])
def test_symbolic_partial_failure_restores_phase_parameters_and_metadata(kind,monkeypatch):
    p=q.Circuit.parameter("p");r=q.Circuit.parameter("r")
    c=q.Circuit.symbolic(3).ry(p,0).evolve(q.I(),time=p)
    c.checkpoint("prefix").register("w",[2,0])
    before=c.to_qiskit();method=getattr(QuantumCircuit,kind)
    def fail(self,*a,**k):
        method(self,*a,**k)
        self.global_phase=r
        raise RuntimeError("native partial failure")
    calls={"h":lambda:c.h([1,2]),"ry":lambda:c.ry([r,p],[1,2]),
           "rzz":lambda:c.rzz([r,p],pairs=[(1,2),(2,0)]),"cx":lambda:c.cx(pairs=[(1,2),(2,0)])}
    with monkeypatch.context() as patch:
        patch.setattr(QuantumCircuit,kind,fail)
        with pytest.raises(RuntimeError):calls[kind]()
    assert c.to_qiskit()==before and c.parameters==(p,)
    assert c.checkpoints=={"prefix":1} and c.registers=={"w":(2,0)}
    c.ry(r,2);before.ry(r,2)
    np.testing.assert_allclose(Operator(c.bind({p:.2,r:.7}).to_qiskit()).data,
                               Operator(before.assign_parameters({p:.2,r:.7})).data,rtol=0,atol=1e-9)

def test_symbolic_batches_do_not_copy_prefix(monkeypatch):
    p=q.Circuit.parameter("p");c=q.Circuit.symbolic(4).ry(p,0)
    with monkeypatch.context() as patch:
        patch.setattr(QuantumCircuit,"copy",lambda *a,**k:pytest.fail("symbolic gate copied prefix"))
        c.h([1,3]).ry([p,2*p],[2,1]).rzz([p,.3],pairs=[(2,3),(1,0)])
    assert len(c.to_qiskit().data)==7 and c.parameters==(p,)
    assert c.bind({p:.2}).num_qubits==4

def test_classical_staging_remains(monkeypatch):
    c=q.Circuit.classical(3,3);raw=c._qc;original=QuantumCircuit.copy;calls=[]
    def copy(self,*a,**k):
        calls.append(self);return original(self,*a,**k)
    monkeypatch.setattr(QuantumCircuit,"copy",copy)
    c.h([1,2])
    assert len(calls)==1 and calls[0] is raw and c._qc is not raw
