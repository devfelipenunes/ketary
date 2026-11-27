"""Single private experimental prepared engine for two exact domains.

Transition: all-input U† post U = pre, phase insensitive.
StateEigen: signed Pauli stabilizes U|0>, NOT an all-input invariant.
Independent preparation budgets for tableau and state; query reservations
shared across the request. No public API change or numerical promotion.
"""
from dataclasses import dataclass,field
from native9 import RustSession,bounds
from independent20 import pauli
from engine import digest
from router27 import Router
from weighted27 import simulate
from weighted25 import expectation,Weighted
from dag22 import simulate as plain_simulate,Limit
from expectation23 import expectation as plain_expectation
from certificate23 import verify_bytes
from spatial_evidence27 import replay as replay_spatial

@dataclass(frozen=True)
class Transition:
    pre:tuple
    post:tuple

@dataclass(frozen=True)
class StateEigen:
    observable:tuple

@dataclass(frozen=True)
class Policy:
    tableau_build_work:int=2_000_000
    state_build_work:int=2_000_000
    state_nodes:int=65536
    prepare_state:bool=False
    state_backend:str="plain"
    def validate(self):
        bounds(4096,self.tableau_build_work);bounds(4096,self.state_build_work)
        if type(self.state_nodes) is not int or not 1<=self.state_nodes<=65536 or type(self.prepare_state) is not bool:raise ValueError("policy")
        if type(self.state_backend) is not str or self.state_backend not in ("plain","phase-weighted"):raise ValueError("state backend")

@dataclass(frozen=True)
class Report:
    status:str
    domain:str
    snapshot:str
    obligation:str
    route:str
    witness:object=None
    evidence:bytes|None=None
    expectation:tuple|None=None
    attempts:tuple=()

@dataclass(frozen=True)
class Batch:
    reports:tuple
    query_reserved:int
    transition_reserved:int
    state_reserved:int
    preparation_reserved:tuple
    @property
    def status(self):
        return "FAIL" if any(r.status=="FAIL" for r in self.reports) else "PASS" if all(r.status=="PASS" for r in self.reports) else "INCONCLUSIVE"

def obligation(n,spec):
    if type(spec) is Transition:
        pauli(n,spec.pre);pauli(n,spec.post)
        return "all-input-transition",digest({"domain":"all-input-transition","pre":spec.pre,"post":spec.post})
    if type(spec) is StateEigen:
        pauli(n,spec.observable)
        return "zero-input-state-eigen",digest({"domain":"zero-input-state-eigen","post":spec.observable})
    raise TypeError("explicit exact contract domain")

def freeze_plain(d):
    """Freeze reachable unweighted nodes as zero-phase edges, charging
    the existing preparation ledger. No mutable Arena escapes."""
    if d is None:return None
    try:
        live=set();todo=[d.root]
        while todo:
            d.charge();i=todo.pop()
            if i in live:continue
            live.add(i)
            if d.nodes[i][0]:todo.extend(d.children(i))
        ids={i:j for j,i in enumerate(sorted(live))}
        rows=[]
        for i in sorted(live):
            d.charge();l,*v=d.nodes[i]
            rows.append((l,(ids[v[0]],0),(ids[v[1]],0)) if l else (0,v[0]))
        return Weighted(d.n,d.k,(ids[d.root],0),tuple(rows))
    except Limit:return None

@dataclass(frozen=True)
class Engine:
    session:RustSession
    policy:Policy=Policy()
    router:Router=field(init=False,repr=False,compare=False)
    state:object=field(init=False,repr=False,compare=False)
    def __post_init__(self):
        if type(self.session) is not RustSession or type(self.policy) is not Policy:raise TypeError("immutable snapshot and policy")
        self.policy.validate()
        p=self.policy;s=self.session
        object.__setattr__(self,"router",Router(s,p.tableau_build_work))
        state=None
        if p.prepare_state and len(s.packed)<=1536:
            if p.state_backend=="phase-weighted":
                state=simulate(s.width,s.packed,max_nodes=p.state_nodes,max_work=p.state_build_work)
            else:
                state=freeze_plain(plain_simulate(s.width,s.packed,wide=True,cap=p.state_nodes,work=p.state_build_work))
        object.__setattr__(self,"state",state)
    @classmethod
    def prepare(cls,circuit,policy=Policy()):
        return cls(RustSession.from_circuit(circuit),policy)
    def verify(self,specs,*,max_work=2_000_000):
        bounds(4096,max_work)
        if type(specs) is not tuple or not 1<=len(specs)<=64:raise ValueError("bounded tuple")
        s=self.session;n=s.width;p=self.policy
        ids=[obligation(n,spec) for spec in specs] # preflight all requests
        trans=[i for i,spec in enumerate(specs) if type(spec) is Transition]
        states=[i for i,spec in enumerate(specs) if type(spec) is StateEigen]
        q=max_work//len(specs);t=q*len(trans);u=q*len(states)
        reports=[None]*len(specs)
        def report(i,status,route,**kw):
            domain,oid=ids[i]
            return Report(status,domain,s.identity,oid,route,**kw)
        if t:
            decisions=self.router.transitions(tuple((specs[i].pre,specs[i].post) for i in trans),max_work=t)
            for i,d in zip(trans,decisions):
                r=d.report
                reports[i]=report(i,r.status,r.route,witness=r.witness,evidence=r.certificate,attempts=d.attempts)
        else:
            for i in trans:reports[i]=report(i,"INCONCLUSIVE","query-budget")
        for i in states:
            if self.state is None or not q:
                reports[i]=report(i,"INCONCLUSIVE","state-unprepared-or-budget");continue
            r=expectation(self.state,specs[i].observable,max_work=q)
            if r.status=="INCONCLUSIVE":
                reports[i]=report(i,r.status,"state-query-budget");continue
            status="PASS" if r.numerator==(1<<r.denominator_power,0) else "FAIL"
            reports[i]=report(i,status,p.state_backend+"-state",expectation=(r.numerator,r.denominator_power))
        return Batch(tuple(reports),t+u,t,u,(p.tableau_build_work,p.state_build_work if p.prepare_state else 0))

def replay_report(session,spec,report,*,max_work=2_000_000):
    """True/False for supported replay routes, None for unavailable/budget.
    State replay uses the alternative DAG backend; spatial replay is the
    same independent-of-Rust spatial algorithm, not a second spatial oracle.
    """
    if type(session) is not RustSession or type(report) is not Report:raise TypeError("request")
    bounds(4096,max_work);n=session.width;g=session.packed
    domain,oid=obligation(n,spec)
    if (report.snapshot,report.domain,report.obligation)!=(session.identity,domain,oid):return False
    if report.status not in ("PASS","FAIL"):return None
    if type(spec) is Transition:
        if report.route=="spatial":
            r=replay_spatial(n,g,spec.pre,spec.post,report.evidence,max_work=max_work)
            return bool(r and r.status==report.status and r.witness==report.witness)
        if report.route=="temporal-certificate":
            return report.status=="PASS" and report.witness is None and verify_bytes(n,g,spec.pre,spec.post,report.evidence,max_work=max_work)
        return None
    if report.route not in ("plain-state","phase-weighted-state") or len(g)>1536:return None
    a=max_work//2;b=max_work-a
    if not a:return None
    if report.route=="plain-state":
        d=simulate(n,g,max_work=a)
        if d is None:return None
        r=expectation(d,spec.observable,max_work=b)
    else:
        d=plain_simulate(n,g,wide=True,work=a)
        if d is None:return None
        r=plain_expectation(d,spec.observable,max_work=b)
    if r.status=="INCONCLUSIVE":return None
    status="PASS" if r.numerator==(1<<r.denominator_power,0) else "FAIL"
    return status==report.status and report.expectation==(r.numerator,r.denominator_power)
