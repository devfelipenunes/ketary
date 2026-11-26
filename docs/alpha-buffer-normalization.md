# Alpha memory and byte-normalization qualification

Research-only, refs #190 #91 #92 #93 #303 #310. No new runtime API,
simulator, dtype, serialization schema or resource limit.

Interpret byte normalization as bounded buffer handling, finite statevector
validation and UTF-8 admission; not amplitude compression. Result already
owns a complex128 snapshot with shape 2**n and norm tolerance 1e-9. Public
inputs still require defensive copies. Native fresh arrays may be adopted
only under existing ownership rules. Never equate payload limits with RSS.

Compare full finite scan against bounded chunks and reusable Boolean scratch,
while preserving the exact vdot norm computation, finiteness and tolerance.
Theoretical Boolean scratch ceiling (not measured total memory): full N bytes,
chunked at most min(N,8192) bytes. At 20 qubits this is 1 MiB vs 8 KiB;
the 16 MiB state itself is unchanged. Test nonfinite values, non-unit norm,
strided and read-only inputs. No shorter scans are accepted for valid data.

Replay accepts strict UTF-8 JSON text with a 1 MiB cap. Compare a full encode
length with ASCII fast length and strict UTF-8 fallback, including lone
surrogates. This is only byte counting, not parsing or schema validation;
preserve the decoder's existing check order and error categories on any
future promotion. Measure the complete decode separately before changing it.

Architecture: keep reusable bounded kernels separate from orchestration.
Any extraction into src requires actual gain, ADR, ownership registry and
import inventory, strict compatibility and CI. No bytecode/unsafe pointer
API, precision changes, native extension or private Qiskit calls.
Profile p50/p95, three seeds, five repeats; 18 independent processes for
RSS, which remains a lifetime peak, not a scratch allocation measurement.
Existing #478 native access and #479 chunking remain independent. Do not
change runtime without evidence; no controlled-host claim.
