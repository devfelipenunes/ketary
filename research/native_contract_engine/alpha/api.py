"""QContract Alpha local candidate. Explicit exact domains; no public release."""
from dataclasses import dataclass,field
from typing import Literal
from ._core.native9 import RustSession
from ._core.contract_forms11 import label_mask
from ._core.candidate28 import Policy,Transition,StateEigen,replay_report
from ._core.qualified30 import CleanInput,RelativeAction,Equivalent,Separable,ZBranch
from ._core.qualified31 import Engine,SumTransition,NoiseAfter,Correctable
from ._core.unified24 import Compact

__version__="0.1.0a0"
Status=Literal["PASS","FAIL","INCONCLUSIVE","UNSUPPORTED"]

def Pauli(label:str)->tuple[int,int,int]:
    """Signed mask from a label, highest wire first, optional leading minus."""
    if type(label) is not str:raise TypeError("Pauli label")
    n=len(label)-int(label.startswith("-"))
    if not 1<=n<=64:raise ValueError("Pauli width")
    return label_mask(label,n)

# A label is a mask, so leading identities are not carried into the spec.
# The prepared circuit validates the mask against its actual width.
def Contract(*,requires:tuple,ensures:tuple)->Transition:
    return Transition(requires,ensures)

@dataclass(frozen=True)
class Result:
    status:Status
    domain:str
    snapshots:tuple
    obligation:str
    reserved:int
    route:str|None
    witness:object
    evidence:bytes|None
    expectation:tuple|None
    _raw:object=field(repr=False,compare=False)
    @property
    def passed(self):return self.status=="PASS"
    def require(self):
        if not self.passed:raise AssertionError(f"{self.status}: {self.domain}")
        return self

def _result(r):
    d=r.detail
    w=getattr(d,"witness",None)
    if type(w) is Compact:w=w.expand()
    evidence=getattr(d,"evidence",None)
    expectation=getattr(d,"expectation",None)
    return Result(r.status,r.domain,r.snapshots,r.obligation,r.reserved,getattr(d,"route",None),w,evidence,expectation,r)

@dataclass(frozen=True)
class Prepared:
    _engine:Engine=field(repr=False)
    @property
    def width(self):return self._engine.base.prepared.session.width
    @property
    def snapshot_id(self):return self._engine.base.prepared.session.identity
    def verify(self,*contracts,max_work=2_000_000)->tuple[Result,...]:
        return tuple(_result(r) for r in self._engine.verify(contracts,max_work=max_work))
    def check(self,contract,*,max_work=2_000_000)->Result:
        return self.verify(contract,max_work=max_work)[0]
    def equivalent_to(self,reference,*,strict=False):
        if type(reference) is not Prepared:raise TypeError("prepared reference")
        return Equivalent(reference._engine.base.prepared.session,strict)
    def action_matches(self,reference,*,ancillas):
        if type(reference) is not Prepared:raise TypeError("prepared reference")
        return RelativeAction(reference._engine.base.prepared.session,ancillas)
    def replay(self,contract,result,*,max_work=2_000_000):
        """Replay supported transition/state routes. None means unavailable."""
        if type(result) is not Result or type(contract) not in (Transition,StateEigen):return None
        raw=result._raw
        if result!=_result(raw):return False
        if raw.detail is None:return None
        return replay_report(self._engine.base.prepared.session,contract,raw.detail,max_work=max_work)

def prepare(circuit,*,prepare_state=False,state_backend="plain",state_fallback=True,
            tableau_build_work=2_000_000,state_build_work=2_000_000,state_nodes=65536)->Prepared:
    """Snapshot a canonical Qiskit QuantumCircuit.

    Exact Clifford+T alphabet, no symbolic/classical operations. Explicit
    source global phase is rejected rather than silently promising strict
    source-phase equality. Logical budgets are not time/memory limits.
    """
    from qiskit import QuantumCircuit
    if type(circuit) is not QuantumCircuit:raise TypeError("Qiskit QuantumCircuit required")
    if circuit.num_parameters or circuit.global_phase!=0:raise ValueError("symbolic or nonzero source global phase unsupported")
    policy=Policy(tableau_build_work=tableau_build_work,state_build_work=state_build_work,state_nodes=state_nodes,
                  prepare_state=prepare_state,state_backend=state_backend,state_fallback=state_fallback)
    policy.validate()
    return Prepared(Engine.prepare(RustSession.from_qiskit(circuit),policy))

__all__=["Pauli","Contract","Transition","StateEigen","CleanInput","Separable","ZBranch",
         "SumTransition","NoiseAfter","Correctable","Prepared","Result","Status","prepare","__version__"]
