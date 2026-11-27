"""QContract Alpha local candidate. Explicit exact domains; no public release."""
from dataclasses import dataclass,field
from typing import Literal
from ._core.native9 import RustSession,bounds
from ._core.independent20 import pauli as _validate_pauli
from ._core.contract_forms11 import label_mask
from ._core.candidate28 import Policy,Transition,StateEigen,replay_report,obligation,Report as CoreReport
from ._core.qualified30 import CleanInput,RelativeAction,Equivalent,Separable,ZBranch,Report as DomainReport
from ._core.qualified31 import Engine,SumTransition,NoiseAfter,Correctable,validate as _validate_spec
from ._core.unified24 import Compact

__version__="0.1.0a3"
Status=Literal["PASS","FAIL","INCONCLUSIVE","UNSUPPORTED"]
Signed=tuple[int,int,int]
Dyadic=tuple[tuple[int,int],int]
Specification=Transition|StateEigen|CleanInput|Separable|ZBranch|SumTransition|NoiseAfter|Correctable|Equivalent|RelativeAction

def Pauli(label:str)->tuple[int,int,int]:
    """Signed mask from a label, highest wire first, optional leading minus."""
    if type(label) is not str:raise TypeError("Pauli label")
    n=len(label)-int(label.startswith("-"))
    if not 1<=n<=64:raise ValueError("Pauli width")
    return label_mask(label,n)

# A label is a mask, so leading identities are not carried into the spec.
# The prepared circuit validates the mask against its actual width.
def Contract(*,requires:Signed,ensures:Signed)->Transition:
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
    diagnostics:tuple
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
    # Stable immutable named pairs for the candidate, not raw research classes.
    extra=[]
    for name in ("coefficient","image","residual","table","reason","detail"):
        if hasattr(d,name):
            value=getattr(d,name)
            if value is not None:extra.append((name,value))
    if r.domain=="zero-input-unnormalized-z-branch" and type(d) is tuple:
        extra.extend((("probability",d[0]),("unnormalized_expectation",d[1])))
    return Result(r.status,r.domain,r.snapshots,r.obligation,r.reserved,getattr(d,"route",None),w,evidence,expectation,tuple(extra),r)

@dataclass(frozen=True)
class Prepared:
    _engine:Engine=field(repr=False)
    @property
    def width(self):return self._engine.base.prepared.session.width
    @property
    def snapshot_id(self):return self._engine.base.prepared.session.identity
    def _state_batch(self,contracts,max_work):
        # Apply the same state route in pure and mixed requests. Admit
        # the entire request first and keep the original per-item quota.
        # Low-budget items and explicit DAG policies retain legacy routing.
        core=self._engine.base.prepared
        table=core.router.previous.prepared.tableau
        if table is None or core.state is not None or not core.policy.state_fallback:return None
        states=tuple(i for i,x in enumerate(contracts) if type(x) is StateEigen)
        q=max_work//len(contracts)
        if not states or not q:return None
        if len(states)==len(contracts):
            keys=tuple((domain,(self.snapshot_id,),oid) for domain,oid in
                       (obligation(self.width,x) for x in contracts))
        else:
            keys=tuple(_validate_spec(core.session,x) for x in contracts)
        eligible=tuple(i for i in states if 3+contracts[i].observable[0].bit_count()+contracts[i].observable[1].bit_count()<=q)
        if not eligible:return None
        images=table.images(tuple(contracts[i].observable for i in eligible),1,q*len(eligible))
        out=[None]*len(contracts)
        for i,(x,z,sign) in zip(eligible,images):
            domain,ids,oid=keys[i]
            value=0 if x else (-1)**sign
            status="PASS" if value==1 else "FAIL"
            detail=CoreReport(status,domain,self.snapshot_id,oid,"tableau-state",expectation=((value,0),0))
            out[i]=DomainReport(status,domain,ids,oid,q,detail)
        rest=tuple(i for i,r in enumerate(out) if r is None)
        if rest:
            raw=self._engine.verify(tuple(contracts[i] for i in rest),max_work=q*len(rest))
            for i,r in zip(rest,raw):out[i]=r
        return tuple(out)
    def verify(self,*contracts:Specification,max_work:int=2_000_000)->tuple[Result,...]:
        bounds(4096,max_work)
        if not 1<=len(contracts)<=64:raise ValueError("bounded tuple")
        raw=self._state_batch(contracts,max_work)
        if raw is None:raw=self._engine.verify(contracts,max_work=max_work)
        return tuple(_result(r) for r in raw)
    def statuses(self,*contracts:Specification,max_work:int=2_000_000)->tuple[Status,...]:
        """Status-only query: no reports or replay evidence returned.

        Preserve all four outcomes and equal per-item budgets. Specialized
        Clifford transition path avoids hashing and witness expansion;
        all other domains use the regular verification route.
        """
        bounds(4096,max_work)
        if not 1<=len(contracts)<=64:raise ValueError("bounded tuple")
        core=self._engine.base.prepared
        table=core.router.previous.prepared.tableau
        if table is None or not all(type(x) is Transition for x in contracts):
            return tuple(r.status for r in self.verify(*contracts,max_work=max_work))
        n=self.width
        for x in contracts:_validate_pauli(n,x.pre);_validate_pauli(n,x.post)
        q=max_work//len(contracts)
        indices=tuple(i for i,x in enumerate(contracts) if 1+x.post[0].bit_count()+x.post[1].bit_count()+2*(2*n+3)<=q)
        out=["INCONCLUSIVE"]*len(contracts)
        if indices:
            raw=table.contracts(tuple((contracts[i].pre,contracts[i].post) for i in indices),q*len(indices))
            for i,v in zip(indices,raw):
                if v is not None:out[i]="PASS" if v[0] else "FAIL"
        return tuple(out)
    def check(self,contract:Specification,*,max_work:int=2_000_000)->Result:
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


def pauli_on(width:int,terms:tuple[tuple[int,str],...],*,negative:bool=False)->Signed:
    """Build a signed Pauli from explicit zero-based wire indices.

    Each wire occurs once. Unspecified wires are identity. As with Pauli(),
    the returned mask is validated against the prepared circuit at query time.
    """
    if type(width) is not int or not 1<=width<=64 or type(terms) is not tuple or type(negative) is not bool or len(terms)>width:raise ValueError("Pauli wire specification")
    x=z=0;seen=set()
    for term in terms:
        if type(term) is not tuple or len(term)!=2:raise ValueError("wire term")
        wire,axis=term
        if type(wire) is not int or not 0<=wire<width or wire in seen or type(axis) is not str or axis not in ("I","X","Y","Z"):raise ValueError("wire or axis")
        seen.add(wire)
        if axis in ("X","Y"):x|=1<<wire
        if axis in ("Z","Y"):z|=1<<wire
    return (x,z,int(negative))

@dataclass(frozen=True)
class Named:
    """A human-readable label attached to an existing exact specification."""
    name:str
    specification:Specification
    def __post_init__(self):
        if type(self.name) is not str or not 1<=len(self.name)<=96 or self.name!=self.name.strip() or not self.name.isprintable():raise ValueError("obligation name")
        if type(self.specification) not in (Transition,StateEigen,CleanInput,RelativeAction,Equivalent,Separable,ZBranch,SumTransition,NoiseAfter,Correctable):raise TypeError("explicit contract specification")

def transition(name:str,*,before:str,after:str)->Named:
    """All-input observable equality U† after U = before."""
    return Named(name,Contract(requires=Pauli(before),ensures=Pauli(after)))
def invariant(name:str,*,observable:str)->Named:
    return transition(name,before=observable,after=observable)
def zero_input(name:str,*,stabilizes:str)->Named:
    """Signed Pauli stabilizes U|0...0>; not an all-input invariant."""
    return Named(name,StateEigen(Pauli(stabilizes)))
def clean_ancillas(name:str,*,wires:tuple[int,...])->Named:
    return Named(name,CleanInput(wires))

@dataclass(frozen=True)
class Outcome:
    results:tuple[tuple[str,Result],...]
    def __post_init__(self):
        if type(self.results) is not tuple or not 1<=len(self.results)<=64 or any(type(x) is not tuple or len(x)!=2 or type(x[0]) is not str or type(x[1]) is not Result for x in self.results):raise ValueError("nonempty named results")
        if len({x[0] for x in self.results})!=len(self.results):raise ValueError("duplicate result name")
    @property
    def passed(self)->bool:return all(r.passed for _,r in self.results)
    def require(self):
        if not self.passed:raise AssertionError("; ".join(f"{name}: {r.status} ({r.domain})" for name,r in self.results if not r.passed))
        return self
    def explain(self)->tuple[dict[str,object],...]:
        meanings={"PASS":"Exact guarantee in the stated domain","FAIL":"Exact refutation in the stated domain",
                  "INCONCLUSIVE":"No proof or refutation within admitted resources","UNSUPPORTED":"Outside supported contract domain"}
        return tuple({"name":name,"status":r.status,"scope":r.domain,"meaning":meanings[r.status],"route":r.route,
                      "snapshot_ids":r.snapshots,"obligation_id":r.obligation,"has_witness":r.witness is not None,
                      "expectation":r.expectation} for name,r in self.results)

@dataclass(frozen=True)
class Plan:
    """A conjunction of named independent obligations, not a sequential proof."""
    obligations:tuple[Named,...]
    def __post_init__(self):
        if type(self.obligations) is not tuple or not 1<=len(self.obligations)<=64 or any(type(x) is not Named for x in self.obligations):raise ValueError("1–64 named obligations")
        if len({x.name for x in self.obligations})!=len(self.obligations):raise ValueError("duplicate obligation name")
    def verify(self,engine:Prepared,*,max_work:int=2_000_000)->Outcome:
        if type(engine) is not Prepared:raise TypeError("prepared engine")
        raw=engine.verify(*(x.specification for x in self.obligations),max_work=max_work)
        return Outcome(tuple(zip((x.name for x in self.obligations),raw)))

__all__=["Pauli","Contract","Transition","StateEigen","CleanInput","Separable","ZBranch",
         "SumTransition","NoiseAfter","Correctable","Prepared","Result","Status","Signed","Dyadic","Specification","prepare","__version__",
         "pauli_on","Named","Plan","Outcome","transition","invariant","zero_input","clean_ancillas"]
