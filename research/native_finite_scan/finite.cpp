#include <cmath>
#include <cstddef>
// Research only. No fast-math, no runtime SDK dependency.
extern "C" int finite_scan(const double* data, std::size_t n) {
    unsigned int valid = 1;
    for (std::size_t i = 0; i < n; ++i)
        valid &= static_cast<unsigned int>(std::isfinite(data[i]));
    return static_cast<int>(valid);
}
