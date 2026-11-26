# Explicit SIMD finite-scan qualification

OPT11, refs #301 #308 #102 #103. Prior native research did not establish
explicit SIMD execution. This x86-64 AVX2-only experiment uses intrinsics
to compare IEEE-754 exponent fields for four double values at once, with
scalar tail checks and runtime CPU capability checks. No fast-math,
undefined unaligned loads, runtime SDK dependency, or architecture
portability claim. Unsupported hosts emit explicit UNSUPPORTED evidence,
not PASS. Independent integer bit-pattern controls cover NaNs (including
signaling encodings), infinities, finite extremes, signed zero, tails and
unaligned contiguous arrays; use the previous 26 scalar finite cases too.

The same nine actual Qiskit binding fixtures compare Python, NumPy,
C++, Rust and explicit AVX2; retain prepacked and complete extraction
costs separately. This is not a simulator or alternate math implementation.
If full validation is slower, do not adopt even if the isolated kernel
is fast. Shared CI, raw p50/p95 only; dedicated host remains outstanding.
