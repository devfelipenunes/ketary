# Application 01 — finite quantum error-model audit

Decision problem: choose between two three-wire repetition codes for an
explicitly supplied finite Pauli error model. The tool does not select
a physical device, infer its noise or guarantee fault-tolerant recovery.

The bit repetition encoder maps the logical basis to |000>, |111>.
The phase repetition encoder maps it to |+++>, |--->. Each encoder
is verified using two stabilizer-image and two logical-operator
obligations for all inputs. A missing entangling edge is a negative
control. The finite code criterion is separately verified using
Correctable, which is circuit-independent, and independently
cross-checked against every Knill–Laflamme matrix pair on the stated
two-dimensional code space.

| Declared error set | Bit repetition | Phase repetition |
|---|---|---|
| Identity and single X errors | PASS | FAIL |
| Identity and single Z errors | FAIL | PASS |
| Identity, X0 and Z0 | FAIL | FAIL |
| Ambiguous single/double errors | FAIL | FAIL |

These are expected classifications until installed-wheel CI runs.
The ambiguous set includes X0 versus X1X2 and Z0 versus Z1Z2; their
products are logical operators on the corresponding repetition code.
A failed code is not an instruction to weaken the supplied error model.

Run `python -I docs/qcontract/applications/finite_error_audit.py` using
the matching installed Alpha wheels. The JSON report records each
code/error-set decision, independent oracle result and violating pairs,
and separate encoder evidence. Recommend only codes with PASS for the
declared model. If none passes, report no qualified candidate.

The finite code criterion is not a verification of syndrome extraction,
a particular recovery circuit, stochastic error rates, or hardware
performance. It does not establish external usability. This application
uses the existing API without changing the method, engine or package.
Record practical friction and request a change only if a demonstrated
application requirement cannot be represented or verified.
