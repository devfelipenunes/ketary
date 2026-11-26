"""Peak RSS in independent processes; Linux ru_maxrss includes imports."""
import argparse
import json
import resource
import subprocess
import sys
from pathlib import Path
import numpy as np
from qiskit.quantum_info import Statevector
import ketary as q
from algorithm_matrix import ghz_native,state_for

def worker(n,variant):
    data=state_for(n,7100)
    c=ghz_native(n)
    sdk=q.from_qiskit(c)
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out=Statevector(data).evolve(c).data.copy() if variant=="native" else sdk.run(initial_state=data).math.statevector()
    after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert abs(np.vdot(out,out).real-1)<1e-9
    return {"n":n,"variant":variant,"payload_bytes":out.nbytes,"pre_run_high_water_kib":before,
            "process_peak_rss_kib":after,"high_water_increase_kib":max(0,after-before)}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--worker",type=int);p.add_argument("--variant");p.add_argument("--label");p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.worker:print(json.dumps(worker(a.worker,a.variant)))
    else:
        rows=[]
        for n in (12,16,20):
            for variant in ("native","ketary"):
                for rep in range(3):
                    raw=subprocess.check_output([sys.executable,__file__,"--worker",str(n),"--variant",variant],text=True)
                    rows.append({"rep":rep,**json.loads(raw)})
        a.output.write_text(json.dumps({"scope":"isolated process high-water RSS; includes input preparation/imports, not allocation delta","revision":a.label,"rows":rows},indent=2))
