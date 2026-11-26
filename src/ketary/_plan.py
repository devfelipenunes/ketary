"""Explicit immutable query plans; execute exactly one native simulation."""
from dataclasses import dataclass,field
from itertools import islice
from ._inspection import _labels
from ._validation import _int,_limit,ResourceLimit

@dataclass(frozen=True,init=False)
class QueryPlan:
    _circuit: str
    _snapshot: object=field(compare=False,repr=False)
    _sizes: tuple[int,int,int]=field(compare=False,repr=False)
    bits: tuple[str,...]
    paulis: tuple[str,...]
    subsystems: tuple[tuple[int,...],...]

    def __init__(self,circuit,*,bits=(),paulis=(),subsystems=()):
        circuit._require_bound()
        n=circuit.num_qubits
        p,e=tuple(_labels(bits)),tuple(_labels(paulis))
        if any(len(v)!=n or set(v)-set("01") for v in p) or any(len(v)!=n or set(v)-set("IXYZ") for v in e):
            raise ValueError("invalid query label")
        selected=[]
        for wires in islice(iter(subsystems),9):
            ws=tuple(_int(w) for w in islice(iter(wires),n+1))
            if not ws or len(ws)>8 or len(set(ws))!=len(ws) or any(w>=n for w in ws):
                raise ValueError("invalid subsystem")
            selected.append(ws)
        if len(selected)>8 or len(set(selected))!=len(selected):
            raise ValueError("expected up to eight distinct subsystems")
        if not p and not e and not selected:
            raise ValueError("query plan requires a query")
        from ._circuit import Circuit
        payload=circuit.to_json()  # retain the same bounded replay admission
        snapshot=Circuit.from_json(payload)  # validate once, retain private owned native program
        sizes=(16*(1<<n),sum(16*(1<<(2*len(ws))) for ws in selected),len(snapshot._qc.data))
        for key,value in (("_circuit",payload),("_snapshot",snapshot),("_sizes",sizes),("bits",p),("paulis",e),("subsystems",tuple(selected))):
            object.__setattr__(self,key,value)

    def estimate(self):
        state,density,gates=self._sizes
        return {"state_payload_bytes":state,"density_output_bytes":density,
                "gate_count":gates,"simulation_count":1,
                "scope":"payload estimates; not total memory or time"}

    def run(self,*,initial_state=None,max_bytes=64*1024**2):
        budget=_int(max_bytes,1)
        sizes=self.estimate()
        if sizes["state_payload_bytes"]+sizes["density_output_bytes"]>budget:
            raise ResourceLimit("planned payload exceeds budget")
        r=self._snapshot.run(initial_state=initial_state,max_bytes=budget)
        evidence=r.evidence(bits=self.bits,paulis=self.paulis)
        matrices=[]
        for wires in self.subsystems:
            matrix=r.math.density_matrix(wires,max_bytes=budget)
            matrices.append({"wires":list(wires),"real":matrix.real.tolist(),"imag":matrix.imag.tolist()})
        return {"schema_version":1,"scope":"one explicit ideal-state simulation",
                "evidence":evidence,"density_matrices":matrices,"estimate":sizes}
