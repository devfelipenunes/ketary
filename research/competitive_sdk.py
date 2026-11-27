"""COMP01: matched public-API circuit microbenchmarks, not a universal ranking."""
import argparse
import importlib.metadata as metadata
import json
import math
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import time

import numpy as np

ROUTES = ("ketary", "qiskit", "cirq", "pennylane")
FAMILIES = ("ghz", "graph", "qft", "variational", "qaoa", "ising", "random")
ATOL = 1e-9


def workload(family, n, seed):
    """Canonical little-endian gate list; no SDK is the reference generator."""
    rng = random.Random(seed)
    ops = []
    def gate(name, *args):
        ops.append((name, args))
    if family == "ghz":
        gate("h", 0)
        for w in range(n - 1):
            gate("cx", w, w + 1)
    elif family == "graph":
        for w in range(n):
            gate("h", w)
        for w in range(n):
            gate("cz", w, (w + 1) % n)
    elif family == "qft":
        gate("x", 0)
        for w in reversed(range(n)):
            gate("h", w)
            for v in reversed(range(w)):
                gate("cp", math.pi / (2 ** (w - v)), w, v)
        for w in range(n // 2):
            gate("swap", w, n - 1 - w)
    elif family == "variational":
        for _ in range(3):
            for w in range(n):
                gate("ry", rng.uniform(-1, 1), w)
                gate("rz", rng.uniform(-1, 1), w)
            for w in range(n - 1):
                gate("cx", w, w + 1)
    elif family in ("qaoa", "ising"):
        for w in range(n):
            gate("h", w)
        for _ in range(2):
            gamma, beta = rng.uniform(-1, 1), rng.uniform(-1, 1)
            for w in range(n - 1):
                gate("cx", w, w + 1)
                gate("rz", gamma, w + 1)
                gate("cx", w, w + 1)
            for w in range(n):
                gate("rx", beta, w)
            if family == "ising":
                for w in range(n):
                    gate("rz", gamma / 3, w)
    elif family == "random":
        for _ in range(8 * n):
            w, v = rng.sample(range(n), 2)
            name = rng.choice(("h", "x", "rx", "ry", "rz", "cx", "cz", "cp", "swap"))
            if name in ("rx", "ry", "rz"):
                gate(name, rng.uniform(-math.pi, math.pi), w)
            elif name == "cp":
                gate(name, rng.uniform(-math.pi, math.pi), w, v)
            elif name in ("cx", "cz", "swap"):
                gate(name, w, v)
            else:
                gate(name, w)
    else:
        raise ValueError(family)
    return ops


def reference(n, ops):
    """Independent vectorized bit-index oracle; no simulator or SDK imports."""
    idx = np.arange(1 << n, dtype=np.int64)
    state = np.zeros(1 << n, dtype=np.complex128)
    state[0] = 1
    for name, args in ops:
        if name in ("cx", "cz", "cp", "swap"):
            a, b = args[-2:]
            both = ((idx >> a) & 1).astype(bool) & ((idx >> b) & 1).astype(bool)
            if name == "cx":
                state = state[idx ^ (((idx >> a) & 1) << b)]
            elif name == "swap":
                state = state[idx ^ ((((idx >> a) ^ (idx >> b)) & 1) * ((1 << a) | (1 << b)))]
            else:
                state[both] *= -1 if name == "cz" else np.exp(1j * args[0])
            continue
        w = args[-1]
        lo = idx[(idx & (1 << w)) == 0]
        hi = lo | (1 << w)
        a, b = state[lo].copy(), state[hi].copy()
        if name == "h":
            state[lo], state[hi] = (a + b) / np.sqrt(2), (a - b) / np.sqrt(2)
        elif name == "x":
            state[lo], state[hi] = b, a
        else:
            t = args[0] / 2
            c, s = np.cos(t), np.sin(t)
            if name == "rx":
                state[lo], state[hi] = c*a-1j*s*b, -1j*s*a+c*b
            elif name == "ry":
                state[lo], state[hi] = c*a-s*b, s*a+c*b
            elif name == "rz":
                state[lo], state[hi] = np.exp(-1j*t)*a, np.exp(1j*t)*b
            else:
                raise ValueError(name)
    return state


def adapter(route, n, ops):
    """Build and execute separately; each returns an owned complex128 array."""
    if route == "ketary":
        import ketary as q
        def build():
            circuit = q.Circuit(n)
            for name, args in ops:
                getattr(circuit, name)(*args)
            return circuit
        return build, lambda c: c.run().math.statevector()
    if route == "qiskit":
        from qiskit import QuantumCircuit
        from qiskit.quantum_info import Statevector
        def build():
            circuit = QuantumCircuit(n)
            for name, args in ops:
                getattr(circuit, name)(*args)
            return circuit
        return build, lambda c: Statevector.from_instruction(c).data.copy()
    if route == "cirq":
        import cirq
        wires = cirq.LineQubit.range(n)
        sim = cirq.Simulator(dtype=np.complex128)
        def build():
            single = {"h": cirq.H, "x": cirq.X}
            rotation = {"rx": cirq.rx, "ry": cirq.ry, "rz": cirq.rz}
            double = {"cx": cirq.CNOT, "cz": cirq.CZ, "swap": cirq.SWAP}
            def operation(name, args):
                if name in single:
                    return single[name](wires[args[0]])
                if name in rotation:
                    return rotation[name](args[0])(wires[args[1]])
                if name == "cp":
                    return cirq.CZPowGate(exponent=args[0]/math.pi)(wires[args[1]], wires[args[2]])
                return double[name](wires[args[0]], wires[args[1]])
            return cirq.Circuit(operation(name, args) for name, args in ops)
        return build, lambda c: sim.simulate(c, qubit_order=list(reversed(wires))).final_state_vector.copy()
    if route == "pennylane":
        import pennylane as qml
        dev = qml.device("default.qubit", wires=list(reversed(range(n))))
        def build():
            gates = {"h": qml.Hadamard, "x": qml.PauliX, "rx": qml.RX,
                     "ry": qml.RY, "rz": qml.RZ, "cx": qml.CNOT, "cz": qml.CZ,
                     "cp": qml.ControlledPhaseShift, "swap": qml.SWAP}
            records = []
            for name, args in ops:
                if name in ("rx", "ry", "rz", "cp"):
                    records.append(gates[name](args[0], wires=args[1:]))
                else:
                    records.append(gates[name](wires=args))
            return qml.tape.QuantumScript(records, [qml.state()])
        def execute(c):
            return np.asarray(qml.execute([c], dev, diff_method=None, interface=None,
                                          cache=False)[0]).copy()
        return build, execute
    raise ValueError(route)


def check(actual, expected):
    if actual.dtype != np.complex128 or actual.shape != expected.shape or not np.isfinite(actual).all():
        raise AssertionError("dtype, shape or finite-value mismatch")
    err = float(np.max(np.abs(actual - expected)))
    norm = float(abs(np.vdot(actual, actual).real - 1))
    if err > ATOL or norm > ATOL:
        raise AssertionError(f"strict state mismatch: max={err}, norm={norm}")
    return {"strict_max": err, "l2": float(np.linalg.norm(actual-expected)),
            "norm_error": norm, "fidelity": float(abs(np.vdot(expected, actual))**2),
            "tv": float(0.5*np.sum(np.abs(np.abs(expected)**2-np.abs(actual)**2)))}


def summary(values):
    return {"raw_ms": values, "median_ms": statistics.median(values),
            "p95_ms": float(np.percentile(values, 95)), "p99_ms": float(np.percentile(values, 99)),
            "mad_ms": statistics.median(abs(v-statistics.median(values)) for v in values)}


def measure(family, n, seed, repetitions):
    ops = workload(family, n, seed)
    expected = reference(n, ops)
    functions, errors = {}, {}
    for route in ROUTES:
        build, execute = adapter(route, n, ops)
        prepared = build()
        errors[route] = check(execute(prepared), expected)
        functions[route] = {"build": build, "execute_owned": lambda e=execute,c=prepared:e(c),
                            "end_to_end": lambda b=build,e=execute:e(b())}
    rng = random.Random(seed+n)
    stages = {}
    for stage in ("build", "execute_owned", "end_to_end"):
        raw = {route: [] for route in ROUTES}
        orders = []
        for i in range(repetitions+3):
            order = list(ROUTES)
            rng.shuffle(order)
            if i >= 3:
                orders.append(order)
            for route in order:
                start = time.perf_counter_ns()
                result = functions[route][stage]()
                elapsed = (time.perf_counter_ns()-start)/1e6
                if i >= 3:
                    raw[route].append(elapsed)
                del result
        stages[stage] = {"order": orders, "samples": {r: summary(v) for r,v in raw.items()},
                         "paired_ketary_over_qiskit": [a/b for a,b in zip(raw["ketary"],raw["qiskit"])]}
    return {"family": family, "n": n, "seed": seed, "gates": len(ops), "ops": ops,
            "semantic": errors, "stages": stages}


def rss_worker(route, family, n, seed):
    ops = workload(family,n,seed)
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    build, execute = adapter(route,n,ops)
    setup = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = execute(build())
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Independent oracle runs after measurement, so it cannot inflate reported peak.
    check(result,reference(n,ops))
    return {"route":route,"family":family,"n":n,"seed":seed,"before_import_kib":before,
            "after_setup_kib":setup,"peak_kib":peak,"peak_delta_kib":peak-setup,
            "payload_bytes":result.nbytes}


def run(seed, repetitions, smoke=False):
    widths = (3,) if smoke else (4,8,12)
    rows = [measure(f,n,seed,repetitions) for f in FAMILIES for n in widths]
    memory = []
    if not smoke:
        tasks = [(r,n,k) for r in ROUTES for n in (8,12) for k in range(3)]
        random.Random(seed).shuffle(tasks)
        for route,n,trial in tasks:
            raw = subprocess.check_output([sys.executable,__file__,"--rss-route",route,
                                           "--rss-width",str(n),"--seed",str(seed)],text=True)
            memory.append({**json.loads(raw),"trial":trial})
    versions = {name:metadata.version(name) for name in
                ("ketary","qiskit","cirq-core","pennylane","numpy","scipy")}
    return {"schema":1,"scope":"shared Linux runner, common gate stream; no general winner",
            "commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "python":sys.version,"platform":platform.platform(),"versions":versions,
            "affinity":sorted(os.sched_getaffinity(0)),"seed":seed,"repetitions":repetitions,
            "thread_env":{k:os.environ.get(k) for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","RAYON_NUM_THREADS")},
            "cases":rows,"rss":memory}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--rss-route",choices=ROUTES)
    p.add_argument("--rss-width",type=int,choices=(8,12),default=8)
    a = p.parse_args()
    if not 3 <= a.repetitions <= 100 or (not a.smoke and a.repetitions < 20):
        p.error("20..100 repetitions; smoke 3..100")
    data = rss_worker(a.rss_route,"random",a.rss_width,a.seed) if a.rss_route else run(a.seed,a.repetitions,a.smoke)
    print(json.dumps(data,indent=2,allow_nan=False))
