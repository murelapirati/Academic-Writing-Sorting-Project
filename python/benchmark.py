"""
benchmark.py
------------
Runs every sorting algorithm against every benchmark dataset.

Each sort runs in an isolated subprocess so it can be hard-killed on timeout
without affecting the main process. Passing the .pkl file path (not the data
itself) to the subprocess avoids pickling large lists through the IPC pipe.

Measures per sort:
  - Wall-clock time   (time.perf_counter)     what you actually wait for
  - CPU time          (resource.getrusage)    pure compute, excludes GC/memory waits
  - Peak memory       (tracemalloc, in KB)    most RAM used at any point during sort

Results are written to results.csv.
"""

import csv
import multiprocessing
import os
import pickle
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.dirname(PROJECT_ROOT)
DATA_DIR     = os.path.join(REPO_ROOT, "data")
RESULTS_FILE = os.path.join(REPO_ROOT, "results_single.csv")
LOG_FILE     = os.path.join(REPO_ROOT, "benchmark_log.txt")
TIMEOUT      = 120  # seconds per individual sort

# Map: algorithm name → (module path, function name)
ALGORITHMS = {
    "bubble_sort":    ("algorithms.bubble_sort",    "bubble_sort"),
    "insertion_sort": ("algorithms.insertion_sort", "insertion_sort"),
    "merge_sort":     ("algorithms.merge_sort",     "merge_sort"),
    "quick_sort":     ("algorithms.quick_sort",     "quick_sort"),
}


# ── Worker (runs inside a subprocess) ─────────────────────────────────────────

def _worker(result_queue, algo_name, pkl_path, project_root):
    """
    Executed in a fresh child process for every single sort.
    Loads the dataset from disk, runs the algorithm, pushes stats back via queue.

    Why subprocess instead of thread?
      - A running thread in Python cannot be forcibly stopped mid-sort.
      - A process can be terminated cleanly with process.terminate().
      - Memory measurements are isolated — no contamination from prior sorts.
      - A crash or stack overflow in one sort can't kill the whole benchmark.
    """
    import importlib
    import time
    import tracemalloc

    sys.path.insert(0, project_root)

    try:
        with open(pkl_path, "rb") as f:
            payload = pickle.load(f)

        # Always sort a fresh copy — never mutate the stored benchmark data.
        arr = list(payload["data"])

        module_name, func_name = ALGORITHMS[algo_name]
        func = getattr(importlib.import_module(module_name), func_name)

        # ── Measure ────────────────────────────────────────────────────────────
        tracemalloc.start()
        t0_wall = time.perf_counter_ns()
        t0_cpu  = time.process_time_ns()

        func(arr)

        wall_ns   = time.perf_counter_ns() - t0_wall
        cpu_ns    = time.process_time_ns()  - t0_cpu
        _, peak_b = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        # ──────────────────────────────────────────────────────────────────────

        result_queue.put({
            "wall_time_ns":   wall_ns,
            "cpu_time_ns":    cpu_ns,
            "peak_memory_kb": peak_b // 1024,
            "error":          None,
        })

    except Exception as exc:
        result_queue.put({"error": str(exc)})


def _run_sort(algo_name, pkl_path):
    """
    Spawns a subprocess, waits up to TIMEOUT seconds, hard-kills if it overruns.
    Returns (stats_dict_or_None, status_string).
    """
    q = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=_worker,
        args=(q, algo_name, pkl_path, PROJECT_ROOT),
    )
    p.start()
    p.join(TIMEOUT)

    if p.is_alive():
        p.terminate()   # hard kill — the sort hit the 2-minute wall
        p.join()
        return None, "TIMEOUT"

    if p.exitcode != 0:
        return None, "ERROR"

    result = q.get()
    if result.get("error"):
        return None, f"ERROR: {result['error']}"

    return result, "ok"


# ── Dataset loader ─────────────────────────────────────────────────────────────

def load_datasets():
    datasets = []
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith(".pkl"):
            continue
        path = os.path.join(DATA_DIR, fname)
        with open(path, "rb") as f:
            payload = pickle.load(f)
        datasets.append({
            "label": payload["label"],
            "n":     payload["n"],
            "path":  path,
        })
    return datasets


# ── Main ───────────────────────────────────────────────────────────────────────

def _fmt_time(ns):
    """Auto-scale a nanosecond integer to a human-readable string."""
    if ns is None:
        return "—"
    if ns < 1_000:
        return f"{ns} ns"
    elif ns < 1_000_000:
        return f"{ns / 1_000:.3f} µs"
    elif ns < 1_000_000_000:
        return f"{ns / 1_000_000:.3f} ms"
    else:
        return f"{ns / 1_000_000_000:.3f} s"


def main():
    log_handle = open(LOG_FILE, "w", encoding="utf-8")

    def emit(line=""):
        print(line)
        log_handle.write(line + "\n")
        log_handle.flush()

    datasets   = load_datasets()
    algo_names = list(ALGORITHMS.keys())
    total      = len(algo_names) * len(datasets)

    emit(f"Benchmark: {len(algo_names)} algorithms × {len(datasets)} datasets = {total} sorts")
    emit(f"Timeout per sort: {TIMEOUT}s")
    emit()

    col = f"{'#':>4}  {'algorithm':<16} {'dataset':<42} {'wall':>12}  {'cpu':>12}  {'mem(KB)':>9}  status"
    emit(col)
    emit("-" * len(col))

    rows = []
    done = 0

    for ds in datasets:
        for algo in algo_names:
            done += 1

            stats, status = _run_sort(algo, ds["path"])

            if stats:
                wall_ns = stats["wall_time_ns"]
                cpu_ns  = stats["cpu_time_ns"]
                mem_kb  = stats["peak_memory_kb"]
                wall_str = _fmt_time(wall_ns)
                cpu_str  = _fmt_time(cpu_ns)
                mem_str  = str(mem_kb)
            else:
                wall_ns = cpu_ns = mem_kb = None
                wall_str = cpu_str = mem_str = "—"

            emit(
                f"{done:>4}  {algo:<16} {ds['label']:<42} "
                f"{wall_str:>12}  {cpu_str:>12}  {mem_str:>9}  {status}"
            )

            rows.append({
                "algorithm":      algo,
                "dataset":        ds["label"],
                "n":              ds["n"],
                "wall_time_ns":   wall_ns,
                "cpu_time_ns":    cpu_ns,
                "peak_memory_kb": mem_kb,
                "status":         status,
            })

    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm", "dataset", "n",
            "wall_time_ns", "cpu_time_ns", "peak_memory_kb", "status",
        ])
        writer.writeheader()
        writer.writerows(rows)

    emit(f"\nDone. Results saved to: {RESULTS_FILE}")
    emit("Run visualize.py to generate charts.")

    log_handle.close()
    print(f"Log saved to: {LOG_FILE}")


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
