# PERF07–13: hardware-performance program

The runtime remains a Qiskit-authoritative Python API. Native experiments
use QuEST 4.2.0 commit 9d7618d7263e3bfba433b88cf1eac0647f08fa0a.

| ID | Experiment | Required evidence |
|---|---|---|
| PERF07 | Aer fusion on/off, mixed and diagonal circuits | Strict states, same thread count, raw timing |
| PERF08 | Portable vs host-native C++ release build | Same CPU, compiler flags, CPU features; no unsupported ISA execution |
| PERF09 | CPU 1/2/4 threads on same runner | Affinity and matched workloads; no cross-machine scaling claims |
| PERF10 | Explicit CUDA and cuQuantum builds | Real supported GPU and strict output checks |
| PERF11 | Reuse native register vs allocate each trial; synchronized init/evolve/export | Transfer and allocation stages; VRAM high-water requires GPU profiler |
| PERF12 | Explicit MPI build, two local ranks; future multi-node trials | All ranks participate; full-state gather for correctness only |
| PERF13 | Dedicated host, controlled affinity and clocks | Repeated independent processes, raw artifacts, host manifest |

The standalone executable uses public QuEST initialization/export APIs;
no direct device pointer or assumed GPU memory layout. Timings include
synchronization; global phase is applied once after final export for
strict state comparison. It retains full input/output per rank and is
bounded to 22 qubits: this is not a scalable distributed storage path.
Kernel timing excludes Python/subprocess and final file I/O; report
process-wall separately. Aer includes submission and output conversion.
Do not compare kernel-only numbers directly to Python end-to-end numbers.

CI uses shared hosts for CPU and MPI smoke. It does not validate CUDA,
cuQuantum, multi-node MPI, dedicated hardware or AVX-512 specifically.
Host-native compiler flags allow supported instructions, but confirm
generated instructions by disassembly/profiler before claiming SIMD use.

## Dedicated-host reproduction

Use a Linux machine with Python 3.12, pinned dependencies, CMake, GCC or
Clang and pinned QuEST source. Install optional Aer matching the project.
Record lscpu, affinity, compiler, kernel, dependency versions, commit,
power/frequency policy and other load. Run portable and host-native
builds with the same settings, alternating order across independent runs.

```sh
git clone https://github.com/QuEST-Kit/QuEST.git /tmp/quest-perf
git -C /tmp/quest-perf checkout --detach 9d7618d7263e3bfba433b88cf1eac0647f08fa0a
cmake -S research/quest_hardware -B /tmp/ketary-cpu -DQUEST_SOURCE=/tmp/quest-perf -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/ketary-cpu --target ketary_hardware_probe -j2
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python research/hardware_performance.py --exe /tmp/ketary-cpu/ketary_hardware_probe --mode cpu --threads 1 2 4 --label cpu-dedicated --output cpu.json --aer
```

For GPU, use a supported CUDA toolkit and GPU, add
-DKETARY_PROBE_CUDA=ON; separately build with
-DKETARY_PROBE_CUQUANTUM=ON when its SDK is available. Run with
--mode gpu --threads 1 and record nvidia-smi, driver/toolkit and GPU
profiler memory/transfer measurements. No automatic device selection.
For MPI, build with -DKETARY_PROBE_MPI=ON and use --mode mpi
--threads 1 --ranks 2. The local harness deliberately rejects more
rank/thread slots than local affinity. Multi-node tests need a separately
reviewed launcher and per-rank memory plan. No production backend.
