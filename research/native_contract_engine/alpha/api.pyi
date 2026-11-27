from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, TypeAlias
from qiskit import QuantumCircuit

Signed: TypeAlias = tuple[int, int, int]
Dyadic: TypeAlias = tuple[tuple[int, int], int]
Status: TypeAlias = Literal["PASS", "FAIL", "INCONCLUSIVE", "UNSUPPORTED"]

def Pauli(label: str) -> Signed: ...
def Contract(*, requires: Signed, ensures: Signed) -> Transition: ...

@dataclass(frozen=True)
class Transition:
    pre: Signed
    post: Signed
@dataclass(frozen=True)
class StateEigen:
    observable: Signed
@dataclass(frozen=True)
class CleanInput:
    ancillas: tuple[int, ...]
@dataclass(frozen=True)
class Separable:
    cut: int
@dataclass(frozen=True)
class ZBranch:
    wire: int
    outcome: int
    observable: Signed
    probability: Dyadic
    expectation: Dyadic
@dataclass(frozen=True)
class SumTransition:
    pre: tuple[tuple[Signed, Fraction], ...]
    post: tuple[tuple[Signed, Fraction], ...]
@dataclass(frozen=True)
class NoiseAfter:
    pre: Signed
    post: Signed
    entries: tuple[tuple[Signed, int], ...]
    denominator: int
    coefficient: Fraction = ...
@dataclass(frozen=True)
class Correctable:
    stabilizers: tuple[Signed, ...]
    errors: tuple[Signed, ...]
# Produced by Prepared methods; not supported direct constructors.
class _Equivalent: ...
class _RelativeAction: ...
Specification: TypeAlias = Transition | StateEigen | CleanInput | Separable | ZBranch | SumTransition | NoiseAfter | Correctable | _Equivalent | _RelativeAction

@dataclass(frozen=True)
class Result:
    status: Status
    domain: str
    snapshots: tuple[str, ...]
    obligation: str
    reserved: int
    route: str | None
    witness: object
    evidence: bytes | None
    expectation: Dyadic | None
    diagnostics: tuple[tuple[str, object], ...]
    @property
    def passed(self) -> bool: ...
    def require(self) -> Result: ...

class Prepared:
    @property
    def width(self) -> int: ...
    @property
    def snapshot_id(self) -> str: ...
    def verify(self, *contracts: Specification, max_work: int = ...) -> tuple[Result, ...]: ...
    def check(self, contract: Specification, *, max_work: int = ...) -> Result: ...
    def equivalent_to(self, reference: Prepared, *, strict: bool = ...) -> _Equivalent: ...
    def action_matches(self, reference: Prepared, *, ancillas: tuple[int, ...]) -> _RelativeAction: ...
    def replay(self, contract: Specification, result: Result, *, max_work: int = ...) -> bool | None: ...
def prepare(circuit: QuantumCircuit, *, prepare_state: bool = ..., state_backend: Literal["plain","phase-weighted"] = ..., state_fallback: bool = ..., tableau_build_work: int = ..., state_build_work: int = ..., state_nodes: int = ...) -> Prepared: ...
__version__: str
