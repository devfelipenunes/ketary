"""Typed access to legacy JSON-compatible report dictionaries.

The dictionary interface is retained deliberately. Reports do not execute or
cache a simulation. Access to evidence parses the already recorded artifact.
"""
import json

class _Report(dict):
    @property
    def status(self):
        return self["status"]

    @property
    def scope(self):
        return self.get("scope","")

    def to_dict(self):
        return json.loads(self.to_json())

    def to_json(self):
        return json.dumps(self,sort_keys=True,allow_nan=False)

    def render(self):
        return self.to_json()

    def require(self):
        if self.status!="PASS":
            raise AssertionError(self.render())
        return self

class ComparisonReport(_Report):
    @property
    def evidence(self):
        from ._verification import Evidence
        value=self.get("evidence")
        return None if value is None else Evidence.from_dict(value)

class DiagnosticReport(_Report):
    pass

class StatisticalReport(_Report):
    pass
