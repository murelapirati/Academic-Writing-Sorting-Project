# C++ Benchmark Suite

This folder mirrors the Python benchmark setup so you can compare Python vs C++ on the same datasets.

## What it includes

- `benchmark_cpp_single`: single-thread benchmark of:
  - `bubble_sort`
  - `insertion_sort`
  - `merge_sort`
  - `quick_sort`
- `benchmark_cpp_parallel`: parallel chunk-sort benchmark of:
  - `parallel_merge_sort`
  - `parallel_quick_sort`
  - `parallel_bubble_sort`
  - `parallel_insertion_sort`

## Dataset compatibility

Python datasets are generated in `../data/*.pkl`.
C++ cannot read pickle directly, so export them to `cpp/data/*.bin` first:

```bash
python3 ../python/export_cpp_data.py
```

This creates:

- `cpp/data/index.tsv`
- `cpp/data/*.bin`

## Build

```bash
cmake -S . -B build
cmake --build build -j
```

## Run

From repo root:

```bash
./cpp/build/benchmark_cpp_single
./cpp/build/benchmark_cpp_parallel
```

Outputs are written next to Python outputs for easy comparison:

- `../results_cpp_single.csv`
- `../results_cpp_parallel.csv`
- `../benchmark_cpp_log.txt`
- `../benchmark_cpp_parallel_log.txt`

## Optional quick-run filter

To limit datasets by size for faster test runs, set `SRT_MAX_N`:

```bash
SRT_MAX_N=1000 ./cpp/build/benchmark_cpp_single
SRT_MAX_N=1000 ./cpp/build/benchmark_cpp_parallel
```
