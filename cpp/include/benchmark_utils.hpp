#pragma once

#include <chrono>
#include <cmath>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>

namespace sorting_cpp {

inline std::string fmt_time_ns(long long ns) {
    if (ns < 1000LL) {
        return std::to_string(ns) + " ns";
    }
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(3);
    if (ns < 1000000LL) {
        oss << static_cast<double>(ns) / 1000.0 << " us";
    } else if (ns < 1000000000LL) {
        oss << static_cast<double>(ns) / 1000000.0 << " ms";
    } else {
        oss << static_cast<double>(ns) / 1000000000.0 << " s";
    }
    return oss.str();
}

template <typename Fn>
inline std::pair<long long, long long> measure_sort_ns(Fn&& fn) {
    const std::clock_t cpu_start = std::clock();
    const auto wall_start = std::chrono::steady_clock::now();

    fn();

    const auto wall_end = std::chrono::steady_clock::now();
    const std::clock_t cpu_end = std::clock();

    const auto wall_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(wall_end - wall_start).count();
    const double cpu_seconds = static_cast<double>(cpu_end - cpu_start) / static_cast<double>(CLOCKS_PER_SEC);
    const auto cpu_ns = static_cast<long long>(std::llround(cpu_seconds * 1e9));

    return {static_cast<long long>(wall_ns), cpu_ns};
}

inline void ensure_stream(std::ofstream& out, const std::string& path) {
    if (!out) {
        throw std::runtime_error("Failed to open file: " + path);
    }
}

}  // namespace sorting_cpp
