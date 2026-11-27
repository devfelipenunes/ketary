"""Contract language usability prototype; intentionally not installed API.

Named obligations, explicit quantifier scopes, one prepared session and
one bounded batch. No weakening of any existing exact contract.
"""
from dataclasses import dataclass
from qcontract import Contract,StateEigen,Pauli,CleanInput,prepare
from qiskit import QuantumCircuit
import json

@dataclass(frozen=True)
class Named:
    name:str
    specification:object
    def __post_init__(self):
        if type(self.name) is not str or not 1<=len(self.name.strip())<=96 or self.name!=self.name.strip():raise ValueError("nonempty trimmed name (<=96 characters)")

def transition(name,*,before,after):
    """All-input conjugation equality U† after U = before."""
    return Named(name,Contract(requires=Pauli(before),ensures=Pauli(after)))
def invariant(name,*,observable):
    return transition(name,before=observable,after=observable)
def zero_input(name,*,stabilizes):
    """The signed Pauli stabilizes U|0...0>; not an all-input invariant."""
    return Named(name,StateEigen(Pauli(stabilizes)))
def clean_ancillas(name,*,wires):
    """No leakage for all states with the specified ancillas initialized to zero."""
    return Named(name,CleanInput(wires))

@dataclass(frozen=True)
class Plan:
    obligations:tuple[Named,...]
    def __post_init__(self):
        if type(self.obligations) is not tuple or not 1<=len(self.obligations)<=64 or any(type(x) is not Named for x in self.obligations):raise ValueError("1–64 named obligations")
        if len({x.name for x in self.obligations})!=len(self.obligations):raise ValueError("duplicate obligation name")
    def verify(self,engine,*,max_work=2_000_000):
        raw=engine.verify(*(x.specification for x in self.obligations),max_work=max_work)
        return Outcome(tuple(zip((x.name for x in self.obligations),raw)))

@dataclass(frozen=True)
class Outcome:
    results:tuple
    @property
    def passed(self):return all(r.status=="PASS" for _,r in self.results)
    def require(self):
        if not self.passed:
            raise AssertionError("; ".join(f"{name}: {r.status} ({r.domain})" for name,r in self.results if r.status!="PASS"))
        return self
    def explain(self):
        meanings={"PASS":"Exact guarantee in the stated domain","FAIL":"Exact refutation in the stated domain",
                  "INCONCLUSIVE":"No proof or refutation within the admitted resources","UNSUPPORTED":"Outside the supported contract domain"}
        return tuple({"name":name,"status":r.status,"scope":r.domain,"meaning":meanings[r.status],"route":r.route,
                      "snapshot_ids":r.snapshots,"obligation_id":r.obligation,"has_witness":r.witness is not None,"expectation":r.expectation}
                     for name,r in self.results)

def main():
    c=QuantumCircuit(2);c.h(0);c.cx(0,1)
    spec=Plan((transition("Hadamard-CNOT observable map",before="IZ",after="XX"),
               zero_input("Bell X correlation",stabilizes="XX"),
               zero_input("Bell Z correlation",stabilizes="ZZ")))
    p=prepare(c);good=spec.verify(p).require();assert len(good.results)==3
    c.z(0);bad=spec.verify(prepare(c));assert not bad.passed
    assert bad.results[1][1].status=="FAIL" and bad.results[2][1].status=="PASS"
    tiny=spec.verify(p,max_work=1);assert all(r.status=="INCONCLUSIVE" for _,r in tiny.results)
    for item in (bad,tiny):
        try:item.require()
        except AssertionError:pass
        else:raise AssertionError("strict policy silently accepted unproved contract")
    try:Plan((spec.obligations[0],spec.obligations[0]))
    except ValueError:pass
    else:raise AssertionError("duplicate name")
    # Distinguish all-input identity from a zero-input eigenproperty.
    identity=prepare(QuantumCircuit(1))
    both=Plan((invariant("Preserves X operator",observable="X"),zero_input("Input is X eigenstate",stabilizes="X"))).verify(identity)
    assert [r.status for _,r in both.results]==["PASS","FAIL"]
    print(json.dumps({"checks":12,"good":good.explain(),"mutant":bad.explain(),"budget":tiny.explain(),"domain_contrast":both.explain(),
                      "scope":"executable syntax prototype using public A4 API, not installed API or usability study"},indent=2))
if __name__=="__main__":main()
