#include <cmath>
#include <cstddef>
#include <immintrin.h>
// Explicit x86-64 AVX2 research kernel, not a runtime dependency.
// The dispatch check is required before calling an AVX2 target function.
extern "C" int avx2_supported() {
    return __builtin_cpu_supports("avx2") != 0;
}
__attribute__((target("avx2")))
static int scan_avx2(const double* data, std::size_t n) {
    const auto exponent = _mm256_set1_epi64x(0x7ff0000000000000LL);
    auto invalid = _mm256_setzero_si256();
    std::size_t i = 0;
    for (; n-i >= 4; i += 4) {
        const auto bits = _mm256_castpd_si256(_mm256_loadu_pd(data+i));
        const auto masked = _mm256_and_si256(bits, exponent);
        invalid = _mm256_or_si256(invalid, _mm256_cmpeq_epi64(masked, exponent));
    }
    bool valid = _mm256_movemask_pd(_mm256_castsi256_pd(invalid)) == 0;
    for (; i < n; ++i) valid &= std::isfinite(data[i]);
    return static_cast<int>(valid);
}
extern "C" int finite_scan(const double* data, std::size_t n) {
    if (!avx2_supported()) return -1;
    return scan_avx2(data,n);
}
