# Alpha formative study: candidate task packet

Protocol under #165; freeze after independent reviewer approval, before recruitment.
No sessions conducted. Participant-facing instructions below are identical across
Ketary and Qiskit routes except installation and neutral API documentation.
Do not give participants the scoring fixtures or authored example solutions.
Use Python 3.12 and recorded exact versions. Allow official documentation;
record assistance consistently. No internet access requirement for execution.

## Participant tasks

### V — Variational optimization
Prepare a two-qubit even-parity trial state using one adjustable rotation and
entangling gate. Minimize the energy of H=a(Z0+Z1)+b X0 X1 by a real classical
optimizer. Report the parameter, final energy, parity, and the procedure to
evaluate a new parameter. Verify against an independently computed eigenvalue
in the even sector. Variant A: a=.43, b=.61; variant B: a=.57, b=.39.

### D — Diagnose a relative phase defect
Two three-wire circuits prepare GHZ from wire zero. The defective circuit has
one unwanted Z operation at the end. Show whether computational probabilities
distinguish them, produce an observable or state witness that distinguishes
them, fix the defect, and rerun the check. A: Z on wire 0; B: Z on wire 2.
Document why a global-phase-insensitive comparison does not remove the defect.

### H — Maintain a Hamiltonian workflow
Build and evaluate exp(-it H) on an explicitly specified normalized input,
with H=a Z0+b Z1+c Z0 Z1. Modify coefficient c and time; keep reusable code.
Report complex output amplitudes, and explain what would need to change for
noncommuting terms. A: a=.37,b=-.19,c=.23,t=.41; update c=.53,t=.29;
input (|00>+i|11>)/sqrt(2). B: a=-.28,b=.47,c=.31,t=.36;
update c=-.16,t=.62; input (|01>-i|10>)/sqrt(2).

## Administration and rubric (reviewer only)

Use the predeclared schedule below, assigned by enrollment slot before
observing performance. Four slots cross route order and variant order;
the fifth is an explicitly unbalanced formative extension. With three
participants, exact four-cell balance is impossible. Do not replace
incomplete sessions to manufacture a balanced outcome.

| Slot | First route / variant | Second route / variant | Task order |
|---|---|---|---|
| 1 | Ketary A | Qiskit B | V-D-H |
| 2 | Qiskit A | Ketary B | D-H-V |
| 3 | Ketary B | Qiskit A | H-V-D |
| 4 | Qiskit B | Ketary A | V-H-D |
| 5 | Ketary A | Qiskit B | H-D-V |

No personal identifiers in assignment records. Reviewer freezes tasks and
scores independently before actual recruitment. The fixed public tasks
are formative; they are not a secret held-out benchmark. Record prior experience, route,
variant, elapsed time to first correct result, attempts, help requests,
unresolved errors, and maintenance time. Same 25-minute cap per task/route;
record timeout as incomplete, not as missing data. No cross-task score
substitution. No personally identifying data in the repository.

Each task has four binary criteria scored by an independent reviewer:
V: normalized even-sector state; correct objective/eigenvalue within 1e-6;
real optimizer; reproducible parameter change.
D: matching distributions; relative-phase witness; correct diagnosis;
repaired circuit matches reference within 1e-9 on prepared input.
H: initial complex vector within 1e-9; modified vector within 1e-9;
reusable parameterization; explicit noncommutation limitation.
Record all raw criterion decisions and reasons. Report completion separately
from time (including censoring), not a statistically generalizable speedup.
Three to five real external developers, consent, anonymized records, independent
review and fixes remain required. No synthetic participants or hardware claims.
