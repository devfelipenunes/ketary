"""I09 local read-only tool adapter, optional MCP stdio entry point.

Only trusted preloaded, immutable replay artifacts are registered. A request
cannot provide arbitrary source, paths, code, or modify the registry.
"""
from types import MappingProxyType
from hashlib import sha256
import json
import ketary as q
from semantic_engineering import semantic_inspect, diagnose
from contracts import Contract


class ReadTools:
    def __init__(self,circuits):
        if len(circuits)>16:
            raise ValueError("at most 16 registered circuits")
        records={}
        for name,c in circuits.items():
            if type(name) is not str or not 1<=len(name)<=64:
                raise ValueError("invalid artifact name")
            page=c.inspect(limit=1)
            if page["num_qubits"]>8 or page["gate_count"]>256:
                raise q.ResourceLimit("registered artifact too large")
            replay=c.to_json()
            records[name]=replay
        self._registry=MappingProxyType(records)

    def _load(self,name):
        if type(name) is not str or name not in self._registry:
            raise ValueError("unknown registered circuit")
        return q.Circuit.from_json(self._registry[name])

    def inspect(self,name:str):
        return semantic_inspect(self._load(name))

    def verify(self,name:str,probabilities:dict[str,float],expectations:dict[str,float],normalized:bool=False):
        c=self._load(name)
        contract=Contract(c.num_qubits,probabilities=probabilities,expectations=expectations,normalized=normalized)
        return contract.verify(c.run()).to_dict()

    def compare(self,observed:str,reference:str,paulis:list[str]):
        return diagnose(self._load(observed),self._load(reference),paulis=paulis).to_dict()

    def manifest(self):
        return {name:sha256(value.encode()).hexdigest() for name,value in self._registry.items()}


def demo_tools():
    return ReadTools({"bell":q.bell(),"phase_error":q.bell().z(0)})


def create_server(tools):
    """Optional dependency; transport integration requires separate smoke test."""
    from mcp.server.fastmcp import FastMCP
    server=FastMCP("Ketary research read tools")
    server.tool(name="inspect_circuit")(tools.inspect)
    server.tool(name="verify_snapshot")(tools.verify)
    server.tool(name="compare_circuits")(tools.compare)
    server.tool(name="artifact_manifest")(tools.manifest)
    return server


if __name__=="__main__":
    # Demo only: no network listener, no untrusted registration.
    create_server(demo_tools()).run(transport="stdio")
