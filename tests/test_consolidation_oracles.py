"""TC03/05/06: independent seeded logical and ownership regression oracles.

Explicit test gate list intentionally independent of the SDK registry.
This is developer-authored regression coverage, not an independent human
or agent evaluation.
"""
import json
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector
from ketary._gate_specs import SPECS
from ketary._result import Result

GATES={
    "h":(1,0),"x":(1,0),"y":(1,0),"z":(1,0),"s":(1,0),"sdg":(1,0),
    "t":(1,0),"tdg":(1,0),"rx":(1,1),"ry":(1,1),"rz":(1,1),
    "cx":(2,0),"cz":(2,0),"swap":(2,0),"ccx":(3,0),"p":(1,1),
    "u":(1,3),"cp":(2,1),"ch":(2,0),"crx":(2,1),"cry":(2,1),
    "crz":(2,1),"sx":(1,0),"sxdg":(1,0),"cy":(2,0),"cswap":(3,0),
    "rxx":(2,1),"ryy":(2,1),"rzz":(2,1),
}

def random_state(n,rng):
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    return v/np.linalg.norm(v)

def strict(a,b):
    np.testing.assert_allclose(a,b,atol=1e-9,rtol=0)

def test_oracle_catalog_covers_registry():
    assert set(GATES)==set(SPECS)
    for name,(width,angles) in GATES.items():
        assert SPECS[name][1:3]==(width,angles)

@pytest.mark.parametrize("name",GATES)
@pytest.mark.parametrize("seed",[1207,2801,7309])
def test_gate_differential(name,seed):
    rng=np.random.default_rng(seed)
    n=4
    width,angles=GATES[name]
    wires=rng.choice(n,width,replace=False).tolist()
    params=rng.uniform(-7,7,angles).tolist()
    native=QuantumCircuit(n,global_phase=.379)
    native.h(3);native.cx(3,0)
    sdk=q.from_qiskit(native)
    getattr(native,name)(*params,*wires)
    getattr(sdk,name)(*params,*wires)
    strict(Operator(native).data,Operator(sdk.to_qiskit()).data)
    state=random_state(n,rng);saved=state.copy()
    expected=Statevector(state).evolve(native).data
    strict(expected,sdk.run(initial_state=state).math.statevector())
    np.testing.assert_array_equal(state,saved)
    strict(Operator(native).data,Operator(q.Circuit.from_json(sdk.to_json()).to_qiskit()).data)

@pytest.mark.parametrize("controls",range(3,8))
def test_mcx_all_supported_arities(controls):
    n=controls+1;rng=np.random.default_rng(4301+controls)
    wires=rng.permutation(n).tolist()
    native=QuantumCircuit(n,global_phase=.23)
    sdk=q.from_qiskit(native)
    native.mcx(wires[:-1],wires[-1]);sdk.mcx(wires[:-1],wires[-1])
    strict(Operator(native).data,Operator(sdk.to_qiskit()).data)
    state=random_state(n,rng)
    strict(Statevector(state).evolve(native).data,sdk.run(initial_state=state).math.statevector())

@pytest.mark.parametrize("seed",[1207,2801,7309])
def test_mixed_program_replay_and_remapped_composition(seed):
    rng=np.random.default_rng(seed)
    source=QuantumCircuit(3,global_phase=.317);sdk=q.from_qiskit(source)
    for _ in range(48):
        name=list(GATES)[int(rng.integers(len(GATES)))]
        width,angles=GATES[name]
        args=(*rng.uniform(-4,4,angles).tolist(),*rng.choice(3,width,replace=False).tolist())
        getattr(source,name)(*args);getattr(sdk,name)(*args)
    target=QuantumCircuit(5,global_phase=.73);target.h(4)
    actual=q.from_qiskit(target)
    mapping=[4,0,2]
    for _ in range(3):target.compose(source,qubits=mapping,inplace=True)
    actual.apply(sdk,wires=mapping,times=3)
    strict(Operator(target).data,Operator(actual.to_qiskit()).data)
    initial=random_state(5,rng);ref=Statevector(initial).evolve(target).data
    strict(ref,actual.run(initial_state=initial).math.statevector())
    restored=q.Circuit.from_json(actual.to_json())
    strict(ref,restored.run(initial_state=initial).math.statevector())
    # Mutating the exported native object must not mutate the SDK program.
    exported=actual.to_qiskit();exported.x(1)
    strict(ref,actual.run(initial_state=initial).math.statevector())

@pytest.mark.parametrize("mode",["owned","borrowed","view","readonly"])
def test_result_native_adoption_isolation(mode):
    base=np.array([1,1j],dtype=np.complex128)/np.sqrt(2)
    expected=base.copy()
    if mode=="owned":
        native=base.copy();result=Result._from_evolution(native)
    elif mode=="borrowed":
        native=base.copy();result=Result._from_evolution(native,borrowed=native)
        native[:]=0
    elif mode=="view":
        native=base.view();result=Result._from_evolution(native)
        base[:]=0
    else:
        native=base.copy();native.flags.writeable=False
        result=Result._from_evolution(native)
        native.flags.writeable=True;native[:]=0
    strict(result.math.statevector(),expected)
    exported=result.math.statevector();exported[:]=0
    strict(result.math.statevector(),expected)

@pytest.mark.parametrize("bad",[float("nan"),float("inf"),1e308])
def test_nonfinite_or_non_normalized_state_rejected(bad):
    with np.errstate(over="ignore",invalid="ignore"):
        with pytest.raises(ValueError):
            Result([bad,0])

def test_run_many_preflights_all_inputs(monkeypatch):
    import ketary._execution as execution
    c=q.bell()
    def forbidden(*args,**kwargs):
        pytest.fail("native execution reached before complete input preflight")
    monkeypatch.setattr(execution,"execute_ideal",forbidden)
    with pytest.raises(ValueError):
        c.run_many(["00",[1,0]])

def test_replay_duplicate_and_nonfinite_rejected():
    payload=q.bell().to_json()
    with pytest.raises(ValueError):
        q.Circuit.from_json(payload.replace('"schema_version":1','"schema_version":1,"schema_version":1'))
    data=json.loads(payload);data["global_phase"]=float("nan")
    with pytest.raises(ValueError):
        q.Circuit.from_json(json.dumps(data))
