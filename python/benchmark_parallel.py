"""
benchmark_parallel.py
---------------------
Benchmarks all parallel sorting variants across datasets.

Measures:
    - Wall-clock time per (algorithm, workers, dataset) combination
    - Speedup vs 1 worker for the same algorithm+dataset
    - Parallel efficiency (speedup / workers)

Results:
    - CSV: results_parallel.csv
    - Text log: benchmark_parallel_log.txt

Dataset policy:
        - Full coverage mode benchmarks all datasets for all algorithms.
        - Default config mirrors the single benchmark's 300 jobs:
            4 algorithms x 75 datasets x 1 worker-count.
"""

import csv
import importlib
import multiprocessing
import os
import pickle
import queue
import signal
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.dirname(PROJECT_ROOT)
DATA_DIR     = os.path.join(REPO_ROOT, "data")
RESULTS_FILE = os.path.join(REPO_ROOT, "results_parallel.csv")
LOG_FILE     = os.path.join(REPO_ROOT, "benchmark_parallel_log.txt")
TIMEOUT      = 120

ALGORITHMS = {
    "parallel_merge_sort": ("algorithms.parallel_merge_sort", "parallel_merge_sort"),
    "parallel_quick_sort": ("algorithms.parallel_quick_sort", "parallel_quick_sort"),
    "parallel_bubble_sort": ("algorithms.parallel_bubble_sort", "parallel_bubble_sort"),
    "parallel_insertion_sort": ("algorithms.parallel_insertion_sort", "parallel_insertion_sort"),
}

# Worker counts to test.
# Current config: [4, 8, 16] => 4 algorithms x 75 datasets x 3 workers = 900 jobs.
MAX_CPUS     = os.cpu_count() or 1
WORKER_COUNTS = [w for w in [4, 8, 16] if w <= MAX_CPUS * 2]

# ── Worker ─────────────────────────────────────────────────────────────────────

def _worker(result_queue, algo_name, pkl_path, num_workers, project_root):
    import sys
    import time
    import pickle
    import importlib
    import os

    sys.path.insert(0, project_root)

    # On POSIX, isolate this benchmark worker and its descendants in a process
    # group so the parent benchmark can terminate the whole tree on timeout.
    if os.name == "posix":
        os.setsid()

    module_name, func_name = ALGORITHMS[algo_name]
    sort_fn = getattr(importlib.import_module(module_name), func_name)

    with open(pkl_path, "rb") as f:
        payload = pickle.load(f)

    arr = list(payload["data"])

    t0 = time.perf_counter_ns()
    sort_fn(arr, workers=num_workers)
    elapsed_ns = time.perf_counter_ns() - t0

    result_queue.put({"wall_time_ns": elapsed_ns, "error": None})


def _run(algo_name, pkl_path, num_workers):
    q = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=_worker,
        args=(q, algo_name, pkl_path, num_workers, PROJECT_ROOT),
    )
    p.start()
    p.join(TIMEOUT)

    if p.is_alive():
        if os.name == "posix":
            # Kill the timed-out worker process group (worker + pool children).
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            p.join(2)
            if p.is_alive():
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        else:
            p.terminate()
        p.join()
        q.close()
        q.join_thread()
        return None, "TIMEOUT"

    if p.exitcode != 0:
        q.close()
        q.join_thread()
        return None, "ERROR"

    try:
        result = q.get(timeout=2)
    except queue.Empty:
        q.close()
        q.join_thread()
        return None, "ERROR: missing worker result"

    q.close()
    q.join_thread()

    if result.get("error"):
        return None, f"ERROR: {result['error']}"
    return result["wall_time_ns"], "ok"


# ── Dataset filter ─────────────────────────────────────────────────────────────

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
    # Truncate existing log immediately so progress is visible from line 1.
    log_handle = open(LOG_FILE, "w", encoding="utf-8")

    def emit(line=""):
        print(line)
        log_handle.write(line + "\n")
        log_handle.flush()

    datasets_by_algo = {algo_name: load_datasets() for algo_name in ALGORITHMS}

    total_jobs = sum(len(ds_list) for ds_list in datasets_by_algo.values()) * len(WORKER_COUNTS)

    emit("Parallel Sorting benchmark")
    emit(f"Machine CPU count: {MAX_CPUS}")
    emit(f"Worker counts to test: {WORKER_COUNTS}")
    emit(f"Algorithms: {', '.join(ALGORITHMS.keys())}")
    emit(f"Total jobs: {total_jobs}")
    emit("Dataset policy:")
    emit("  - all algorithms: all datasets (all types and sizes)")
    emit(f"Timeout per sort: {TIMEOUT}s")
    emit()

    col = (
        f"{'algorithm':<24} {'workers':>7}  {'dataset':<42} "
        f"{'wall':>12}  {'speedup':>8}  {'efficiency':>10}  status"
    )
    emit(col)
    emit("-" * len(col))

    rows = []

    for algo_name in ALGORITHMS:
        datasets = datasets_by_algo[algo_name]

        emit(f"[{algo_name}] datasets: {len(datasets)}")

        for ds in datasets:
            # Baseline: first worker count — speedups relative to it.
            baseline_ns = None

            for workers in WORKER_COUNTS:
                elapsed_ns, status = _run(algo_name, ds["path"], workers)

                if status == "ok" and elapsed_ns is not None:
                    if workers == WORKER_COUNTS[0]:
                        baseline_ns = elapsed_ns

                    if baseline_ns and elapsed_ns:
                        speedup = round(baseline_ns / elapsed_ns, 3)
                        efficiency = round(speedup / workers, 3)
                    else:
                        speedup = efficiency = None

                    time_str = _fmt_time(elapsed_ns)
                    spd_str = f"{speedup:.3f}" if speedup else "—"
                    eff_str = f"{efficiency:.3f}" if efficiency else "—"
                else:
                    elapsed_ns = speedup = efficiency = None
                    time_str = spd_str = eff_str = "—"

                emit(
                    f"{algo_name:<24} {workers:>7}  {ds['label']:<42} {time_str:>12}  "
                    f"{spd_str:>8}  {eff_str:>10}  {status}"
                )

                rows.append({
                    "algorithm": algo_name,
                    "workers": workers,
                    "dataset": ds["label"],
                    "n": ds["n"],
                    "wall_time_ns": elapsed_ns,
                    "speedup": speedup,
                    "efficiency": efficiency,
                    "status": status,
                })

            emit()

    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm", "workers", "dataset", "n", "wall_time_ns", "speedup", "efficiency", "status",
        ])
        writer.writeheader()
        writer.writerows(rows)

    emit(f"Results saved to: {RESULTS_FILE}")
    emit("Run visualize.py to generate charts.")

    log_handle.close()

    print(f"Log saved to: {LOG_FILE}")


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
