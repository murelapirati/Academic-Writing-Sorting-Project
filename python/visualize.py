"""
visualize.py
------------
Reads results_single.csv, results_bogo.csv, and results_parallel.csv
and produces charts saved into a charts/ folder.

Charts produced:
  Single-core:
  1.  wall_time_by_n_int.png      — Wall time vs n for random integers
  2.  wall_time_by_n_str.png      — Same, but for random strings
  3.  wall_time_by_n_tup.png      — Same, but for random tuples
  4.  shapes_medium_int.png       — Bar chart: data shapes at n=10,000 (integers)
  5.  shapes_medium_str.png       — Same for strings
  6.  shapes_medium_tup.png       — Same for tuples
  7.  memory_by_n_int.png         — Peak memory vs n for random integers
  8.  memory_by_n_str.png         — Same for strings
  9.  memory_by_n_tup.png         — Same for tuples
  10. cpu_vs_wall.png             — CPU vs wall time scatter (GC overhead)

  Bogosort (if results_bogo.csv exists):
  11. bogo_shuffles.png           — Shuffle count distribution per n
  12. bogo_vs_theory.png          — Observed average vs n! theory

  Parallel (if results_parallel.csv exists):
  13. parallel_wall_time.png      — Wall time vs workers per dataset
  14. parallel_speedup.png        — Speedup vs workers (ideal=linear dashed)
  15. parallel_efficiency.png     — Efficiency vs workers (ideal=1.0 dashed)
"""

import csv
import math
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")   # no display needed — saves files directly
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.dirname(ROOT)

# Prefer C++ benchmark results if available
RESULTS          = os.path.join(REPO_ROOT, "results_cpp_single.csv")
if not os.path.exists(RESULTS):
    RESULTS = os.path.join(REPO_ROOT, "results_single.csv")

BOGO_RESULTS     = os.path.join(REPO_ROOT, "results_bogo.csv")

PARALLEL_RESULTS = os.path.join(REPO_ROOT, "results_cpp_parallel.csv")
if not os.path.exists(PARALLEL_RESULTS):
    PARALLEL_RESULTS = os.path.join(REPO_ROOT, "results_parallel.csv")

CHARTS_DIR  = os.path.join(REPO_ROOT, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
COLORS = {
    "bubble_sort":    "#e74c3c",
    "insertion_sort": "#e67e22",
    "merge_sort":     "#2ecc71",
    "quick_sort":     "#3498db",
}
MARKERS = {
    "bubble_sort":    "o",
    "insertion_sort": "s",
    "merge_sort":     "^",
    "quick_sort":     "D",
}
PRETTY = {
    "bubble_sort":    "Bubble Sort",
    "insertion_sort": "Insertion Sort",
    "merge_sort":     "Merge Sort",
    "quick_sort":     "Quick Sort",
}

plt.rcParams.update({
    "figure.dpi":      120,
    "font.size":       10,
    "axes.titlesize":  12,
    "axes.labelsize":  10,
    "legend.fontsize": 9,
})


# ── CSV loader ─────────────────────────────────────────────────────────────────

def load_results(path):
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row["n"] = int(row["n"])
            # Support both new (nanoseconds int) and old (seconds float) CSV formats.
            if "wall_time_ns" in row:
                row["wall_time_s"] = int(row["wall_time_ns"]) / 1e9 if row["wall_time_ns"] else None
                row["cpu_time_s"]  = int(row["cpu_time_ns"])  / 1e9 if row["cpu_time_ns"]  else None
            else:
                row["wall_time_s"] = float(row["wall_time_s"]) if row["wall_time_s"] else None
                row["cpu_time_s"]  = float(row["cpu_time_s"])  if row["cpu_time_s"]  else None
            row["peak_memory_kb"] = int(row["peak_memory_kb"])   if row["peak_memory_kb"] else None
            rows.append(row)
    return rows


def load_bogo(path):
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row["n"]        = int(row["n"])
            row["shuffles"] = int(row["shuffles"])
            row["time_s"]   = float(row["time_s"])
            row["success"]  = row["success"].strip().lower() == "true"
            rows.append(row)
    return rows


# ── Helpers ────────────────────────────────────────────────────────────────────

def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved  {name}")


def _algo_rows(rows, dataset_contains, metric):
    """
    Group rows by algorithm for rows whose dataset label contains `dataset_contains`.
    If multiple trials exist for the same (algo, n), results are averaged.
    Returns dict: algo_name → sorted list of (n, value) for rows with status 'ok'.
    """
    # raw_data: algo -> n -> [values]
    raw_data = defaultdict(lambda: defaultdict(list))
    
    for r in rows:
        label = r["dataset"].lower()
        if dataset_contains.lower() in label and r["status"] == "ok":
            val = r[metric]
            if val is not None:
                raw_data[r["algorithm"]][r["n"]].append(val)
    
    grouped = defaultdict(list)
    for algo, n_map in raw_data.items():
        for n, values in n_map.items():
            avg_val = sum(values) / len(values)
            grouped[algo].append((n, avg_val))
            
    for algo in grouped:
        grouped[algo].sort()
    return grouped


# ── Chart 1-3: Wall time vs n (random data, by type) ──────────────────────────

def chart_wall_time_by_n(rows, type_key, type_label, filename):
    """
    Line chart: wall-clock time vs n for random data of the given type.
    Algorithms that timed out on a size simply have no point at that n.
    """
    grouped = _algo_rows(rows, f"{type_label}: Random", "wall_time_s")
    if not grouped:
        print(f"  skipped {filename} — no data")
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    for algo, points in sorted(grouped.items()):
        ns, times = zip(*points)
        ax.plot(
            ns, times,
            label=PRETTY.get(algo, algo),
            color=COLORS.get(algo, "grey"),
            marker=MARKERS.get(algo, "o"),
            linewidth=2, markersize=5,
        )
        # Mark any missing sizes (timeouts) so the viewer knows there is data
        # — it just didn't finish.

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n (list size, log scale)")
    ax.set_ylabel("Wall-clock time (seconds, log scale)")
    ax.set_title(f"Wall-clock time vs n  |  Random {type_label}s")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    save(fig, filename)


# ── Chart 4: Data shapes at medium n ──────────────────────────────────────────

def chart_shapes_medium(rows, type_label, filename):
    """
    Grouped bar chart: wall time for each algorithm across data shapes, at n=10,000.
    Shows how each algorithm reacts to sorted, reverse, nearly-sorted, etc.
    """
    # Shapes we care about — labels must substring-match dataset labels
    shapes = ["Random", "Sorted", "Reverse", "Nearly Sorted", "Duplicates",
              "Mixed Case", "Dup Scores"]

    n_target = 10_000
    algo_names = list(COLORS.keys())

    # shape → algo → time
    data = {s: {} for s in shapes}
    for r in rows:
        if r["n"] != n_target or r["status"] != "ok" or r["wall_time_s"] is None:
            continue
        label = r["dataset"]
        if type_label.lower() not in label.lower():
            continue
        algo = r["algorithm"]
        for shape in shapes:
            if shape.lower() in label.lower():
                data[shape][algo] = r["wall_time_s"]
                break

    # Drop shapes with no data for this type
    present_shapes = [s for s in shapes if data[s]]
    if not present_shapes:
        print(f"  skipped {filename} — no data")
        return

    import numpy as np
    x      = np.arange(len(present_shapes))
    n_algo = len(algo_names)
    width  = 0.8 / n_algo

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, algo in enumerate(algo_names):
        heights = [data[s].get(algo, 0) for s in present_shapes]
        bars = ax.bar(
            x + (i - n_algo / 2 + 0.5) * width,
            heights, width,
            label=PRETTY.get(algo, algo),
            color=COLORS.get(algo, "grey"),
            alpha=0.85,
        )
        # Label bars that are zero (timeout) with "T/O"
        for bar, shape in zip(bars, present_shapes):
            val = data[shape].get(algo)
            if val is None or val == 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    ax.get_ylim()[1] * 0.02,
                    "T/O", ha="center", va="bottom", fontsize=7, color="red",
                )

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(present_shapes, rotation=15, ha="right")
    ax.set_ylabel("Wall-clock time (seconds, log scale)")
    ax.set_title(f"Wall time by data shape  |  {type_label}  |  n={n_target:,}")
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    save(fig, filename)


# ── Chart 5: Peak memory vs n ─────────────────────────────────────────────────

def chart_memory(rows, type_label, filename):
    grouped = _algo_rows(rows, f"{type_label}: Random", "peak_memory_kb")
    if not grouped:
        print(f"  skipped {filename} — no data")
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    for algo, points in sorted(grouped.items()):
        ns, mems = zip(*points)
        ax.plot(
            ns, mems,
            label=PRETTY.get(algo, algo),
            color=COLORS.get(algo, "grey"),
            marker=MARKERS.get(algo, "o"),
            linewidth=2, markersize=5,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n (list size, log scale)")
    ax.set_ylabel("Peak memory (KB, log scale)")
    ax.set_title(f"Peak memory usage vs n  |  Random {type_label}s")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    save(fig, filename)


# ── Chart 6: CPU time vs wall time scatter ────────────────────────────────────

def chart_cpu_vs_wall(rows, filename):
    """
    Scatter: x=CPU time, y=wall time. Points above the diagonal (y=x) mean the
    sort spent time waiting (GC, memory allocation) beyond pure CPU work.
    """
    fig, ax = plt.subplots(figsize=(7, 7))

    for algo in COLORS:
        pts = [
            (r["cpu_time_s"], r["wall_time_s"])
            for r in rows
            if r["algorithm"] == algo
            and r["status"] == "ok"
            and r["cpu_time_s"] is not None
            and r["wall_time_s"] is not None
        ]
        if not pts:
            continue
        cx, wy = zip(*pts)
        ax.scatter(cx, wy, label=PRETTY.get(algo, algo),
                   color=COLORS[algo], alpha=0.6, s=25)

    # Diagonal y = x (wall == cpu, no overhead)
    lim = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([0, lim], [0, lim], "k--", linewidth=1, alpha=0.5, label="wall = cpu")

    ax.set_xlabel("CPU time (s)")
    ax.set_ylabel("Wall-clock time (s)")
    ax.set_title("CPU time vs Wall-clock time\n(above diagonal = time spent on allocation/GC)")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)

    save(fig, filename)


# ── Chart 7: Bogosort shuffle distribution ────────────────────────────────────

def chart_bogo_shuffles(bogo_rows, filename):
    """
    Scatter of every trial's shuffle count, with the per-n mean overlaid.
    Shows both the luck variance and the average growth.
    """
    import numpy as np

    ns_all   = [r["n"]        for r in bogo_rows if r["success"]]
    shuf_all = [r["shuffles"] for r in bogo_rows if r["success"]]

    if not ns_all:
        print(f"  skipped {filename} — no successful bogo trials")
        return

    # Per-n averages
    by_n = defaultdict(list)
    for r in bogo_rows:
        if r["success"]:
            by_n[r["n"]].append(r["shuffles"])
    ns_avg   = sorted(by_n)
    avg_shuf = [sum(by_n[n]) / len(by_n[n]) for n in ns_avg]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.scatter(ns_all, shuf_all, alpha=0.35, s=20, color="#9b59b6", label="Individual trials")
    ax.plot(ns_avg, avg_shuf, "o-", color="#8e44ad", linewidth=2,
            markersize=6, label="Average shuffles")

    ax.set_xlabel("n (list size)")
    ax.set_ylabel("Shuffles until sorted")
    ax.set_title("Bogosort — shuffles per trial vs n\n(only successful runs shown)")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    save(fig, filename)


# ── Chart 8: Bogosort average vs n! theory ───────────────────────────────────

def chart_bogo_vs_theory(bogo_rows, filename):
    """
    Line chart comparing observed average shuffles against the theoretical
    expected value of n! (or more precisely (n+1)! / 2 — but n! is the intuitive
    upper-bound people quote, so we plot both).
    """
    by_n = defaultdict(list)
    for r in bogo_rows:
        if r["success"]:
            by_n[r["n"]].append(r["shuffles"])

    ns       = sorted(by_n)
    observed = [sum(by_n[n]) / len(by_n[n]) for n in ns]
    theory   = [math.factorial(n) for n in ns]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(ns, observed, "o-", color="#8e44ad", linewidth=2,
            markersize=6, label="Observed average shuffles")
    ax.plot(ns, theory,   "s--", color="#c0392b", linewidth=1.5,
            markersize=5, label="n!  (theoretical expected)")

    ax.set_yscale("log")
    ax.set_xlabel("n (list size)")
    ax.set_ylabel("Shuffles (log scale)")
    ax.set_title("Bogosort: observed average vs theoretical n!\n"
                 "(observed ≈ n! confirms the O(n·n!) expected behaviour)")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    save(fig, filename)


# ── Parallel CSV loader ───────────────────────────────────────────────────────

def load_parallel(path):
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row["workers"]     = int(row["workers"])
            row["n"]           = int(row["n"])
            # Support both new (nanoseconds int) and old (seconds float) CSV formats.
            if "wall_time_ns" in row:
                row["wall_time_s"] = int(row["wall_time_ns"]) / 1e9 if row["wall_time_ns"] else None
            else:
                row["wall_time_s"] = float(row["wall_time_s"]) if row["wall_time_s"] else None
            row["speedup"]     = float(row["speedup"])     if row["speedup"]     else None
            row["efficiency"]  = float(row["efficiency"])  if row["efficiency"]  else None
            rows.append(row)
    return rows


# ── Chart 13: Wall time vs workers ────────────────────────────────────────────

def chart_parallel_wall_time(par_rows, filename):
    """
    Line chart: wall time vs number of workers, one line per dataset.
    Shows whether adding cores actually reduces time.
    """
    by_dataset = defaultdict(list)
    for r in par_rows:
        if r["status"] == "ok" and r["wall_time_s"] is not None:
            by_dataset[r["dataset"]].append((r["workers"], r["wall_time_s"]))

    if not by_dataset:
        print(f"  skipped {filename} — no data")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    cmap = plt.get_cmap("tab10")

    for i, (label, points) in enumerate(sorted(by_dataset.items())):
        points.sort()
        ws, ts = zip(*points)
        ax.plot(ws, ts, "o-", label=label, color=cmap(i % 10), linewidth=2, markersize=5)

    ax.set_xlabel("Number of worker processes")
    ax.set_ylabel("Wall-clock time (seconds)")
    ax.set_title("Parallel Merge Sort — wall time vs workers")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    save(fig, filename)


# ── Chart 14: Speedup vs workers ──────────────────────────────────────────────

def chart_parallel_speedup(par_rows, filename):
    """
    Speedup = time_1_worker / time_N_workers.
    Ideal (linear) speedup is plotted as a dashed reference line.
    Real speedup is always below ideal due to Amdahl's Law.
    """
    by_dataset = defaultdict(list)
    for r in par_rows:
        if r["status"] == "ok" and r["speedup"] is not None:
            by_dataset[r["dataset"]].append((r["workers"], r["speedup"]))

    if not by_dataset:
        print(f"  skipped {filename} — no data")
        return

    all_workers = sorted({r["workers"] for r in par_rows})

    fig, ax = plt.subplots(figsize=(9, 5))
    cmap = plt.get_cmap("tab10")

    # Ideal linear speedup reference
    ax.plot(all_workers, all_workers, "k--", linewidth=1, alpha=0.5, label="Ideal (linear)")

    for i, (label, points) in enumerate(sorted(by_dataset.items())):
        points.sort()
        ws, sp = zip(*points)
        ax.plot(ws, sp, "o-", label=label, color=cmap(i % 10), linewidth=2, markersize=5)

    ax.set_xlabel("Number of worker processes")
    ax.set_ylabel("Speedup  (1-worker time / N-worker time)")
    ax.set_title("Parallel Merge Sort — speedup vs workers\n"
                 "(dashed = ideal linear; real = limited by sequential merge phase)")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    save(fig, filename)


# ── Chart 15: Efficiency vs workers ───────────────────────────────────────────

def chart_parallel_efficiency(par_rows, filename):
    """
    Efficiency = speedup / workers.  Ideal = 1.0 (every core fully utilised).
    In practice efficiency drops as workers increase due to:
      - Sequential merge overhead (Amdahl)
      - Process spawn and IPC costs
      - Memory bandwidth contention
    """
    by_dataset = defaultdict(list)
    for r in par_rows:
        if r["status"] == "ok" and r["efficiency"] is not None:
            by_dataset[r["dataset"]].append((r["workers"], r["efficiency"]))

    if not by_dataset:
        print(f"  skipped {filename} — no data")
        return

    all_workers = sorted({r["workers"] for r in par_rows})

    fig, ax = plt.subplots(figsize=(9, 5))
    cmap = plt.get_cmap("tab10")

    # Ideal efficiency = 1.0
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1, alpha=0.5, label="Ideal efficiency (1.0)")

    for i, (label, points) in enumerate(sorted(by_dataset.items())):
        points.sort()
        ws, eff = zip(*points)
        ax.plot(ws, eff, "o-", label=label, color=cmap(i % 10), linewidth=2, markersize=5)

    ax.set_ylim(0, 1.2)
    ax.set_xlabel("Number of worker processes")
    ax.set_ylabel("Parallel efficiency  (speedup / workers)")
    ax.set_title("Parallel Merge Sort — efficiency vs workers\n"
                 "(1.0 = perfect; drops as merge overhead and spawn cost dominate)")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    save(fig, filename)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(RESULTS):
        print(f"No results file found at {RESULTS}")
        print("Run benchmark_single.py first.")
        return

    print(f"Loading {RESULTS} ...")
    rows = load_results(RESULTS)
    print(f"  {len(rows)} rows loaded.\n")

    print("Generating single-core charts ...")

    # Wall time vs n — one chart per data type
    chart_wall_time_by_n(rows, "int", "Int",   "wall_time_by_n_int.png")
    chart_wall_time_by_n(rows, "str", "Str",   "wall_time_by_n_str.png")
    chart_wall_time_by_n(rows, "tup", "Tuple", "wall_time_by_n_tup.png")

    # Data shapes at medium n
    chart_shapes_medium(rows, "Int",   "shapes_medium_int.png")
    chart_shapes_medium(rows, "Str",   "shapes_medium_str.png")
    chart_shapes_medium(rows, "Tuple", "shapes_medium_tup.png")

    # Peak memory
    chart_memory(rows, "Int",   "memory_by_n_int.png")
    chart_memory(rows, "Str",   "memory_by_n_str.png")
    chart_memory(rows, "Tuple", "memory_by_n_tup.png")

    # CPU vs wall time
    chart_cpu_vs_wall(rows, "cpu_vs_wall.png")

    # Bogosort charts (optional)
    if os.path.exists(BOGO_RESULTS):
        print(f"\nLoading {BOGO_RESULTS} ...")
        bogo = load_bogo(BOGO_RESULTS)
        print(f"  {len(bogo)} rows loaded.\n")
        chart_bogo_shuffles(bogo, "bogo_shuffles.png")
        chart_bogo_vs_theory(bogo, "bogo_vs_theory.png")
    else:
        print(f"\n  (no bogo results — run benchmark_bogo.py to generate them)")

    # Parallel charts (optional)
    if os.path.exists(PARALLEL_RESULTS):
        print(f"\nLoading {PARALLEL_RESULTS} ...")
        par = load_parallel(PARALLEL_RESULTS)
        print(f"  {len(par)} rows loaded.\n")
        print("Generating parallel charts ...")
        chart_parallel_wall_time(par,  "parallel_wall_time.png")
        chart_parallel_speedup(par,    "parallel_speedup.png")
        chart_parallel_efficiency(par, "parallel_efficiency.png")
    else:
        print(f"\n  (no parallel results — run benchmark_parallel.py to generate them)")

    print(f"\nAll charts saved to: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
