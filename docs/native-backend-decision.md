# RFC — Native backend promotion decision (NO-GO)

Refs #308 #103 #89 #96 #98. Decision at integrated revision 30bd5da7:
retain the Qiskit-authoritative runtime. No installed alternate backend,
new dependency, ABI promise, hardware execution or public selection API.
This is an engineering no-go decision, not independent approval for
promotion, licensing clearance or distribution authorization.

## Evidence registry

| Route | Pin and boundary | Existing qualification | Decision |
|---|---|---|---|
| Qiskit Statevector | Qiskit 2.6.2, Python 3.12 | Default, existing public and mathematical tests | Retain |
| Qiskit C API | 2.6.2 experimental public headers, GIL-held CircuitData borrow, native-endian byte rows | [C API audit](qiskit-capi-audit.md), 8-gate construction; 11-gate read-only packing, exact sequence/phase and rejected custom/open/control/malformed input | Research only |
| QuEST v2 bridge | QuEST commit 9d7618d7263e3bfba433b88cf1eac0647f08fa0a, C++17, ABI 2, 24 int32 columns, float64 scalar, complex128 output | [extended native](https://github.com/devfelipenunes/ketary/actions/runs/45766497621), [ABI sanitizer](https://github.com/devfelipenunes/ketary/actions/runs/45766497643), three seeded jobs and standalone ABI oracle | Research only |
| Prepared/forced/direct packing | Same pinned QuEST and Qiskit | [BENCH04](https://github.com/devfelipenunes/ketary/actions/runs/45764869707), [BENCH07](https://github.com/devfelipenunes/ketary/actions/runs/45766023430), [prepared native](prepared-native-batch.md), [translation ablation](translation-ablation.md) | Research only |
| Standalone Rust/C++/AVX2 | Research toolchains recorded, no SDK dependency | [#385](https://github.com/devfelipenunes/ketary/pull/385), [#392](https://github.com/devfelipenunes/ketary/pull/392) | Reject FFI for finite scan |

Historical run results were reviewed: nine BENCH04 jobs, nine BENCH07
jobs, three extended jobs and one native ABI job succeeded. Their artifacts
are historical, not new measurements or current full SDK coverage.
The extended regression checks all 15 gate kinds against all 32 basis
vectors at width five, nonzero global phase, arbitrary complex input,
source mutation, independent batch rows, read-only packed bytes and
defensive snapshot export. MCX is Python packing only, not Rust coverage.
ABI sanitizer covers address/undefined behavior on its executed cases,
not arbitrary hostile pointers or a proof of memory safety. The current
PR adds null-pointer, invalid arity, first-angle and empty-phase controls
and re-triggers the existing pinned sanitizer and extended workflows.

## ABI, coverage, ownership and failure semantics

- The Qiskit C API is experimental; pin 2.6.2, no private Rust symbol or
  object-layout assumptions. The probe does access QuantumCircuit._data
  to pass CircuitData to the documented borrow API. Treat that Python
  attribute as a version-sensitive boundary, not public stable ABI.
- Extended CPU v2 is a same-process private native-endian layout, not a
  persistence format: 96 topology bytes/gate plus 8 angle bytes, widths
  1..22, <=100000 instructions, <=256 rows, <=128 MiB output payload and
  <=64 MiB angle table. Fresh outputs, CPU register allocated per call,
  one environment per process, wrapper lock. Borrowed pointers require
  trusted callers and valid buffer lengths. Direct C callers must supply
  normalized finite input and correct-sized nonoverlapping buffers;
  raw pointer lengths/aliasing are not verifiable from this ABI alone.
- Supported subset is bound, gate-only, plain logical circuits. Open
  controls, custom gates, classical/dynamic data, layout, metadata and
  unbound parameters reject rather than silently falling back. ABI
  mismatch and initialization/close/execute errors are explicit.
  No translation of native faults into a verified success.
- Public Circuit, Result and Observable contracts remain unchanged.
  No global mutable runtime cache or implicit parallelism. An optional
  backend would need an explicit lifecycle and resource design; existing
  research locks do not establish SDK thread safety.

## Performance and memory evidence

BENCH07 reported 282/282 supported case/input/runner medians favoring
direct over Qiskit Statevector, but only 47/108 original cases supported
direct packing. BENCH04 gate ratios against Statevector: prepared QuEST
0.309/0.307/0.227, Rust-packed QuEST 0.314/0.312/0.232, full lowering
2.117/2.187/1.787 (three runners). Raw p50/p95, stages and exclusions
remain in the cited artifacts. Ratios are per-runner historical
diagnostics, not a universal speedup or current apples-to-apples SDK
release benchmark. Preparation, conversion, output copy, and failure
handling matter. The AVX2 finite-scan study passed 1228 bit-pattern
controls but full validation lost in all nine fixtures; faster isolated
kernels do not justify a runtime dependency. Process RSS in #391 covers
composition and sweep, not QuEST allocator or GPU VRAM.

## Licensing and portability

Qiskit 2.6.2 upstream LICENSE.txt is Apache-2.0; pinned QuEST
[LICENCE.txt](https://github.com/QuEST-Kit/QuEST/blob/9d7618d7263e3bfba433b88cf1eac0647f08fa0a/LICENCE.txt)
is MIT (copyright and permission notice must accompany copies/substantial
portions). This is a source-license inspection, not a full binary,
transitive license, patent, or redistribution review. The existing
[third-party review](third-party-review.md) covers declared installed
metadata and outstanding artifact obligations. Research sources are not
a new wheel dependency; packaging checks forbid compiled libraries.
Windows/macOS SDK smoke is not native bridge qualification. Native
Linux shared CI is not dedicated hardware, GPU/cuQuantum, or multi-node
MPI qualification.

## Go/no-go gates for any later proposal

| Gate | Current status |
|---|---|
| Pinned version/ABI and explicit direct subset | Bounded research evidence |
| Strict mathematical/phase and negative controls | Bounded research evidence |
| Native memory safety and portable wheel/ABI strategy | Not established beyond tested research cases |
| Dedicated matched end-to-end p50/p95, CPU affinity, peak RSS | Blocked on authorized host (#256 #309 #310) |
| GPU/cuQuantum/MPI multi-node support | Not qualified (#102); not a requirement for CPU research |
| Complete license/notice and artifact review | Open (#110) |
| Explicit resource/error/lifecycle contract and independent review | Not approved |
| Explicit owner approval for optional backend or release | Not granted |

**NO-GO** for promotion. This closes the scoped research/RFC deliverables
once their exact-head qualification is integrated; it does not close
hardware, legal, release, or independent review gates. No extra backend
or automatic fallback is implemented. Reopen a promotion proposal only
with a concrete supported workload, controlled evidence, and explicit
authorization.
