cmake_minimum_required(VERSION 3.16)
project(sorting_cpp_benchmarks LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(benchmark_cpp_single
    src/benchmark_single.cpp
)
target_include_directories(benchmark_cpp_single PRIVATE include)

add_executable(benchmark_cpp_parallel
    src/benchmark_parallel.cpp
)
target_include_directories(benchmark_cpp_parallel PRIVATE include)
