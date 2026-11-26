import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Statevector
from ketary._verification import _outputs

@pytest.mark.parametrize("label",["000","101","+-r","l1-"])
def test_pair_shares_only_immutable_input(label,monkeypatch):
    a=q.Circuit(3).h(0).cx(0,2);b=a.copy().rz(.17,1)
    real=q.Circuit.run;seen=[]
    def spy(self,**kwargs):
        seen.append(kwargs["initial_state"])
        return real(self,**kwargs)
    monkeypatch.setattr(q.Circuit,"run",spy)
    x,y=_outputs(a,b,label,64*1024**2)
    assert len(seen)==2 and seen[0] is seen[1] and isinstance(seen[0],q.Result)
    initial=Statevector.from_label(label)
    for c,r in ((a,x),(b,y)):
        np.testing.assert_allclose(r._data,initial.evolve(c.to_qiskit()).data,atol=1e-9,rtol=0)
        assert not np.shares_memory(r._data,seen[0]._data)
    assert not np.shares_memory(x._data,y._data)

def test_subclass_retains_array_input():
    class Tracked(q.Circuit):
        def run(self,**kwargs):
            assert type(kwargs["initial_state"]) is np.ndarray
            return super().run(**kwargs)
    _outputs(Tracked(2),q.Circuit(2),"++",64*1024**2)

def test_minimization_reuses_input_and_preserves_witness(monkeypatch):
    a=q.Circuit(2).x(0).x(0).z(1);b=q.Circuit(2)
    evidence=a.test.compare(b,inputs=["++"],complete=False).evidence
    real=q.Circuit.run;seen=[]
    def spy(self,**kwargs):
        seen.append(kwargs["initial_state"])
        return real(self,**kwargs)
    monkeypatch.setattr(q.Circuit,"run",spy)
    reduced=evidence.minimize(max_attempts=16)
    assert len(seen)>=3 and all(s is seen[0] for s in seen) and isinstance(seen[0],q.Result)
    assert reduced["status"]=="FAIL"
    assert q.Evidence.from_dict(reduced["evidence"]).reproduce()["reproduced"]
