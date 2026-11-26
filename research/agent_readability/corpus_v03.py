"""Public, deterministic KetaryEval v0.3 calibration corpus.

The 180 cases are parameterized task instances, not 180 independent task
families or a hidden evaluation set. No submitted Python is executed.
"""
from collections import Counter
from ketary_eval import CASES as LEGACY, FRAMEWORKS, source

TARGET = {
    "generation": 30, "comprehension": 30, "mathematics": 20,
    "debugging": 20, "repair": 20, "testing": 20,
    "optimization": 20, "abstention": 20,
}


def build_cases():
    cases = [dict(c, kind="debugging" if c["kind"] == "diagnosis" else c["kind"],
                  family="legacy-" + c["id"]) for c in LEGACY]

    def add(kind, family, n, request, **kwargs):
        prefixes = {"generation": "G", "comprehension": "C", "mathematics": "M",
                    "debugging": "D", "repair": "R", "testing": "T",
                    "optimization": "O", "abstention": "A"}
        i = 1 + sum(c["kind"] == kind for c in cases)
        cases.append(dict(id=f"{prefixes[kind]}{i:02}", kind=kind, family=family,
                          n=n, request=request, **kwargs))

    def label(n, value):
        return format(value, f"0{n}b")

    def code(kind, family, n, gates, mutant, **kwargs):
        request = kwargs.pop("request", f"Implement the full ordered operator {gates!r}. "
                             "Preserve strict global phase.")
        add(kind, family, n, request, gates=gates, mutant=mutant, **kwargs)

    # Generation: directed control, signed rotations, relative phase, swaps,
    # non-Clifford phase and multi-control, with distinct wire/angle choices.
    for i in range(26):
        n = 3 + i % 2
        a, b, c = [(i+j) % n for j in range(3)]
        theta = round(.17 + .07*i, 2)
        variants = [
            ("directed-control", [("h",a),("cx",a,b)], [("h",a),("cx",b,a)]),
            ("rotation-sign", [("ry",theta,a),("rz",-.3,b)], [("ry",-theta,a),("rz",-.3,b)]),
            ("relative-phase", [("h",a),("cx",a,b),("z",a)], [("h",a),("cx",a,b)]),
            ("wire-permutation", [("x",a),("swap",a,b)], [("x",a),("swap",a,c)]),
            ("non-clifford", [("h",a),("t",a),("cx",a,b)], [("h",a),("tdg",a),("cx",a,b)]),
            ("multi-control", [("x",a),("x",b),("ccx",a,b,c)], [("x",a),("x",b),("ccx",a,c,b)]),
        ]
        family, gates, mutant = variants[i % len(variants)]
        # A distinct trailing rotation supplies a controlled perturbation per instance.
        tail = ("rx", theta, c)
        code("generation", family, n, gates+[tail], mutant+[tail])

    for i in range(26):
        n = 3 + i // 6
        a, b, c = [(i+j) % n for j in range(3)]
        theta = round(.11 + .03*i, 2)
        mode = i % 4
        if mode == 0:
            ops = [("x",a),("cx",a,b),("swap",b,c)]
            answer = label(n, (1<<a)|(1<<c))
            add("comprehension","basis-label",n,"Return the unique Z-basis measurement label from zero input, highest wire first.",
                source=ops, answer=answer, wrong=label(n,1<<a))
        elif mode == 1:
            ops = [("ry",theta,a),("cx",a,b),("rz",-theta,c)]
            add("comprehension","ordered-wires",n,"Return [[gate, ordered wires], ...], excluding rotation angles.",
                source=ops, answer=[["ry",[a]],["cx",[a,b]],["rz",[c]]],
                wrong=[["ry",[a]],["cx",[b,a]],["rz",[c]]])
        elif mode == 2:
            ref = [("h",a),("cx",a,b),("rx",theta,c)]
            add("comprehension","phase-vs-distribution",n,
                f"Reference ordered gates: {ref!r}. Return [same Z distribution, same state up to global phase] as booleans.",
                source=ref+[("z",a)], reference_gates=ref, answer=[True,False], wrong=[True,True])
        else:
            ops = [("x",a),("x",b),("ccx",a,b,c)]
            add("comprehension","toffoli",n,"Return the unique measurement label from zero input, highest wire first.",
                source=ops, answer=label(n,(1<<a)|(1<<b)|(1<<c)), wrong=label(n,(1<<a)|(1<<b)))

    # Exact, analytically specified probability/Pauli cases (no rounding of
    # free-form model prose). The spectator qubits also test label conventions.
    for i in range(20):
        n = 3 + i//5
        a, b = i % n, (i+1) % n
        family = i % 4
        if family == 0:
            ops = [("h",a),("h",b)]
            add("mathematics","probability",n,"From zero input return the exact probability of the all-zero label as a JSON number.",
                source=ops, answer=.25, wrong=.5)
        elif family == 1:
            ops = [("h",a),("cx",a,b),("z",a)]
            pauli = "".join("X" if w in (a,b) else "I" for w in reversed(range(n)))
            add("mathematics","pauli-relative-phase",n,f"Return the exact expectation of Pauli {pauli} as an integer.",
                source=ops, answer=-1, wrong=1, pauli=pauli)
        elif family == 2:
            ops = [("h",a),("cx",a,b)]
            pauli = "".join("Z" if w in (a,b) else "I" for w in reversed(range(n)))
            add("mathematics","pauli-parity",n,f"Return the exact expectation of Pauli {pauli} as an integer.",
                source=ops, answer=1, wrong=0, pauli=pauli)
        else:
            ops = [("h",a),("cx",a,b)]
            pauli = "".join("Z" if w==a else "I" for w in reversed(range(n)))
            add("mathematics","local-marginal",n,f"Return the exact expectation of Pauli {pauli} as an integer.",
                source=ops, answer=0, wrong=1, pauli=pauli)

    for i in range(19):
        n = 3 + i//7
        a, b = i % n, (i+1) % n
        # The target a is still zero when the divergent operation is reached.
        prefix = [("h",b)] + [("rz",round(.09*(j+1),2),b) for j in range(i%5)]
        ref = prefix+[("x",a),("cx",a,b)]
        obs = prefix+[("z",a),("cx",a,b)]
        add("debugging","first-state-divergence",n,
            f"Reference ordered gates: {ref!r}. Return [first divergent zero-input state checkpoint up to global phase, observed gate], initial index 0.",
            source=obs, reference_gates=ref, answer=[len(prefix)+1,"z"], wrong=[len(prefix),"h"])

    for i in range(17):
        n = 3 + i%2
        a,b,c = [(i+j)%n for j in range(3)]
        theta = round(.21+.04*i,2)
        variants = [
            ("control-reversal",[("h",a),("cx",a,b)],[("h",a),("cx",b,a)]),
            ("rotation-sign",[("rx",theta,a),("ry",-theta,b)],[("rx",theta,a),("ry",theta,b)]),
            ("phase-repair",[("h",a),("cx",a,b)],[("h",a),("cx",a,b),("z",a)]),
            ("toffoli-target",[("x",a),("ccx",a,b,c)],[("x",a),("ccx",a,c,b)]),
        ]
        family,gates,bad = variants[i%4]
        tail=[("rz",theta,c)]
        code("repair",family,n,gates+tail,bad+tail,source=bad+tail,
             request=f"Repair the source to implement exactly the full operator {gates+tail!r}.")

    # A structured test is a basis-input/output assertion that must pass the
    # intended operator and fail the mutant. Alternative valid tests accepted.
    for i in range(20):
        n=3+i//5
        a,b=i%n,(i+1)%n
        if i%2:
            good=[("cx",a,b)]
            bad=[("cx",b,a)]
        else:
            good=[("x",b),("cx",a,b)]
            bad=[("x",b)]
        inp=1<<a
        out=inp ^ (1<<b) if i%2 else inp
        badout=inp if i%2 else inp ^ (1<<b)
        add("testing","basis-mutant-kill",n,
            f"Intended ordered gates: {good!r}. Submit a single deterministic basis test "
            "as [input_label, expected_output_label] that passes the intended operator and fails the observed source. Highest wire first.",
            source=bad, intended=good, answer=[label(n,inp),label(n,out)],
            wrong=[label(n,inp),label(n,badout)])

    for i in range(20):
        n=3+i//5
        a,b=i%n,(i+1)%n
        theta=round(.13+.03*i,2)
        pairs=[
            [("h",a),("h",a)], [("s",a),("sdg",a)],
            [("rx",theta,a),("rx",-theta,a)], [("cx",a,b),("cx",a,b)],
            [("t",b),("tdg",b)],
        ]
        pair=pairs[i%5]
        target=[("ry",theta,b),("cx",b,a)]
        original=pair+target
        code("optimization","adjacent-inverse",n,target,original,source=original,
             max_count=2,request="Return a circuit of at most two gates equivalent to the entire source operator, with strict global phase.")

    # Balanced literal-reader classification, not a claim about general Python.
    for i in range(20):
        n=3+i//5
        a,b=i%n,(i+1)%n
        if i%2==0:
            suffix=[
                "rx(theta, 0)", "h(0 + 1)", "cx(0, 0)",
                "measure(0, 0)", "ry(0.2, wire=0)",
            ][(i//2)%5]
            expected="UNSUPPORTED"
        else:
            suffix=f"rx({round(.12+.05*i,2)}, {a})"
            expected="PASS"
        add("abstention","literal-reader-scope",n,
            "Can the restricted literal reader establish this circuit? Return PASS or UNSUPPORTED as a JSON string. Judge the reader's scope, not general Python validity.",
            source=[("h",b)], suffix=suffix, answer=expected,
            wrong="PASS" if expected=="UNSUPPORTED" else "UNSUPPORTED")

    assert Counter(c["kind"] for c in cases)==TARGET
    assert len({c["id"] for c in cases})==len(cases)==180
    return cases


CASES=build_cases()


def source_for(case, framework):
    text=source(framework,case["n"],case.get("source",[]))
    if "suffix" in case:
        text+="\n"+("c.gates." if framework=="ketary" else "c.")+case["suffix"]
    return text
