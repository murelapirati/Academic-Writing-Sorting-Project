"""
sort_visualizer.py
------------------
Animated bar chart showing each algorithm sorting a small array step by step.

Usage:
    python3 sort_visualizer.py                  # animates all 4 algorithms
    python3 sort_visualizer.py bubble            # just bubble sort
    python3 sort_visualizer.py merge --save      # saves as GIF instead of showing live

Bar colours:
    white  — untouched element
    yellow — currently being compared
    red    — being swapped / placed
    green  — final sorted position (done frame)

Speed is controlled by the DELAY_MS constant below.
"""

import sys
import os
import random

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)

sys.path.insert(0, PROJECT_ROOT)
from algorithms.sort_steps import (
    bubble_sort_steps,
    insertion_sort_steps,
    merge_sort_steps,
    quick_sort_steps,
)

# ── Configuration ──────────────────────────────────────────────────────────────
N         = 40          # number of elements to sort (keep ≤ 60 for clarity)
DELAY_MS  = 40          # milliseconds between frames (lower = faster)
SEED      = 42          # fixed seed so all algorithms sort identical data

ALGORITHMS = {
    "bubble":    ("Bubble Sort",    bubble_sort_steps),
    "insertion": ("Insertion Sort", insertion_sort_steps),
    "merge":     ("Merge Sort",     merge_sort_steps),
    "quick":     ("Quick Sort",     quick_sort_steps),
}

# Colour for each action label
ACTION_COLOURS = {
    "compare":  "#f1c40f",   # yellow
    "swap":     "#e74c3c",   # red
    "shift":    "#e74c3c",   # red
    "place":    "#e74c3c",   # red
    "insert":   "#2ecc71",   # green
    "pick key": "#3498db",   # blue
    "done":     "#2ecc71",   # green (all bars)
}
DEFAULT_BAR_COLOUR = "#ecf0f1"   # off-white


# ── Animator ───────────────────────────────────────────────────────────────────

def animate_algorithm(title, step_gen, save_as=None):
    steps = list(step_gen)          # collect all frames up front
    total = len(steps)

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    first_arr = steps[0][0]
    n = len(first_arr)
    bars = ax.bar(range(n), first_arr, color=DEFAULT_BAR_COLOUR, width=0.8)

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(0, max(first_arr) * 1.1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    title_text = ax.set_title(
        f"{title}  —  step 1 / {total}",
        color="white", fontsize=13, pad=10
    )
    action_text = ax.text(
        0.5, 0.97, "", transform=ax.transAxes,
        ha="center", va="top", color="#bdc3c7", fontsize=10
    )
    counter_text = ax.text(
        0.01, 0.97, "", transform=ax.transAxes,
        ha="left", va="top", color="#7f8c8d", fontsize=9
    )

    comparisons = [0]
    swaps       = [0]

    def update(frame_idx):
        arr, highlights, action = steps[frame_idx]

        if action == "compare":
            comparisons[0] += 1
        elif action in ("swap", "place", "insert"):
            swaps[0] += 1

        for i, bar in enumerate(bars):
            if action == "done":
                bar.set_height(arr[i])
                bar.set_color("#2ecc71")
            elif i in highlights:
                bar.set_height(arr[i])
                bar.set_color(ACTION_COLOURS.get(action, "#e74c3c"))
            else:
                bar.set_height(arr[i])
                bar.set_color(DEFAULT_BAR_COLOUR)

        title_text.set_text(f"{title}  —  step {frame_idx + 1} / {total}")
        action_text.set_text(f"action: {action}")
        counter_text.set_text(f"comparisons: {comparisons[0]}   swaps/writes: {swaps[0]}")
        return bars

    anim = animation.FuncAnimation(
        fig, update,
        frames=total,
        interval=DELAY_MS,
        blit=False,
        repeat=False,
    )

    plt.tight_layout()

    if save_as:
        print(f"  Saving {save_as} ({total} frames) ...")
        anim.save(save_as, writer="pillow", fps=1000 // DELAY_MS)
        print(f"  Saved.")
        plt.close(fig)
    else:
        plt.show()
        plt.close(fig)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args     = sys.argv[1:]
    save_gif = "--save" in args
    args     = [a for a in args if not a.startswith("--")]

    # Which algorithms to run
    if args:
        keys = [a.lower() for a in args if a.lower() in ALGORITHMS]
        if not keys:
            print(f"Unknown algorithm(s). Choose from: {', '.join(ALGORITHMS)}")
            sys.exit(1)
    else:
        keys = list(ALGORITHMS)

    # Build the data (same for every algorithm so comparisons are fair)
    random.seed(SEED)
    data = random.sample(range(1, N * 3), N)

    os.makedirs(os.path.join(REPO_ROOT, "charts"), exist_ok=True)

    for key in keys:
        title, step_fn = ALGORITHMS[key]
        print(f"Visualizing: {title}  ({len(list(step_fn(data[:])))} steps)")

        save_path = None
        if save_gif:
            save_path = os.path.join(REPO_ROOT, "charts", f"anim_{key}.gif")

        animate_algorithm(title, step_fn(list(data)), save_as=save_path)


if __name__ == "__main__":
    main()
