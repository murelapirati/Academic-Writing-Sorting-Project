"""
benchmark_bogo.py
-----------------
Dedicated benchmark for Bogosort.

Because bogosort is non-deterministic, a single run per size is meaningless —
you need multiple trials to see the distribution of luck. This script runs
TRIALS_PER_SIZE independent trials for each n and records:
  - shuffles per trial (min, max, average)
  - time per trial
  - how many trials hit the timeout

Results are saved to results_bogo.csv for charting in visualize.py.
"""

import csv
import os
import random
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)

sys.path.insert(0, PROJECT_ROOT)
from algorithms.bogo_sort import bogo_sort

# ── Configuration ──────────────────────────────────────────────────────────────

# Sizes to test. Bogosort degrades catastrophically — don't go too high.
# The benchmark will auto-stop increasing n once a size has > 50% timeouts.
SIZES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

TRIALS_PER_SIZE = 20    # independent runs per n
TIMEOUT_SECONDS = 120   # 2-minute limit per individual trial

RESULTS_FILE = os.path.join(REPO_ROOT, "results_bogo.csv")

# ── Benchmark ──────────────────────────────────────────────────────────────────

def run_bogo_benchmark():
    rows = []

    print(f"Bogosort benchmark — {TRIALS_PER_SIZE} trials per size, {TIMEOUT_SECONDS}s timeout\n")
    print(f"{'n':>4}  {'trial':>5}  {'shuffles':>12}  {'time (s)':>10}  {'ok?':>5}")
    print("-" * 46)

    for n in SIZES:
        timeouts_this_size = 0

        for trial in range(1, TRIALS_PER_SIZE + 1):
            # Fresh random list of n distinct integers each trial.
            data = random.sample(range(n * 10 + 1), n)

            result = bogo_sort(data, timeout_seconds=TIMEOUT_SECONDS)

            status = "ok" if result["success"] else "TIMEOUT"
            if not result["success"]:
                timeouts_this_size += 1

            print(
                f"{n:>4}  {trial:>5}  {result['shuffles']:>12,}  "
                f"{result['time']:>10.4f}  {status:>5}"
            )

            rows.append({
                "n":        n,
                "trial":    trial,
                "shuffles": result["shuffles"],
                "time_s":   round(result["time"], 6),
                "success":  result["success"],
            })

        # If more than half the trials timed out, further sizes are pointless.
        if timeouts_this_size > TRIALS_PER_SIZE // 2:
            print(f"\n  !! More than 50% of trials timed out at n={n}. Stopping here.")
            break

        print()  # blank line between sizes

    # ── Write CSV ──────────────────────────────────────────────────────────────
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["n", "trial", "shuffles", "time_s", "success"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults saved to: {RESULTS_FILE}")
    print("Run visualize.py to generate the bogosort charts.")


if __name__ == "__main__":
    run_bogo_benchmark()
