"""Trusted deterministic diagnostic example, not an LLM agent.

Two explicit executions; report all checks and distinguish zero-input
evidence from full-operator verification. No arbitrary code evaluation.
"""
import ketary as q

def investigate(reference,observed,*,bits):
    a,b=reference.inspect(),observed.inspect()
    expected,actual=reference.run(),observed.run()
    distribution=actual.test.distribution(expected)
    state=actual.test.state(expected)
    operator=observed.test.equivalent(reference)
    diagnosis=observed.debug.compare(reference)
    return {"reference":a,"observed":b,"evidence":actual.evidence(bits=bits),
        "checks":{"distribution":distribution.to_dict(),"state":state.to_dict(),"operator":operator.to_dict()},
        "diagnosis":diagnosis.to_dict(),
        "scope":"explicit ideal simulation and bounded operator comparison; not root-cause proof"}

def demo():
    reference=q.bell()
    # Equal-length explicit comparison with a phase-error mutant.
    reference.h(0).h(0)
    observed=q.bell().h(0).z(0)
    return investigate(reference,observed,bits=["00","11"])

if __name__=="__main__":
    import json
    print(json.dumps(demo(),indent=2,allow_nan=False))
