"""
parallel_sort_visualizer.py
--------------------------
Parallel visualization of sorting algorithms.
Features:
1. --compare: Side-by-side comparison of multiple algorithms.
2. --parallel: Visualization of a parallel algorithm's chunks.

Usage:
    python3 python/parallel_sort_visualizer.py --compare bubble insertion merge quick
    python3 python/parallel_sort_visualizer.py --parallel merge --workers 4
"""

import sys
import os
import random
import argparse

import matplotlib.pyplot as plt
import matplotlib.animation as animation

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from algorithms.sort_steps import (
    bubble_sort_steps,
    insertion_sort_steps,
    merge_sort_steps,
    quick_sort_steps,
    parallel_merge_sort_steps,
)

# ── Configuration ──────────────────────────────────────────────────────────────
N         = 40
DELAY_MS  = 50
SEED      = 42

ALGORITHMS = {
    "bubble":    ("Bubble Sort",    bubble_sort_steps),
    "insertion": ("Insertion Sort", insertion_sort_steps),
    "merge":     ("Merge Sort",     merge_sort_steps),
    "quick":     ("Quick Sort",     quick_sort_steps),
}

PARALLEL_ALGORITHMS = {
    "merge": ("Parallel Merge Sort", parallel_merge_sort_steps),
}

ACTION_COLOURS = {
    "compare":  "#f1c40f",   # yellow
    "swap":     "#e74c3c",   # red
    "shift":    "#e74c3c",   # red
    "place":    "#e74c3c",   # red
    "insert":   "#2ecc71",   # green
    "pick key": "#3498db",   # blue
    "split":    "#9b59b6",   # purple
    "done":     "#2ecc71",   # green
}
DEFAULT_BAR_COLOUR = "#ecf0f1"

# ── Visualizer ─────────────────────────────────────────────────────────────────

def visualize_mixed(tasks, data, workers=4, save_as=None):
    """
    tasks: list of (key, is_parallel)
    """
    num_tasks = len(tasks)
    cols = 2 if num_tasks > 1 else 1
    rows = (num_tasks + 1) // 2

    fig, axes = plt.subplots(rows, cols, figsize=(min(16, 6*cols), 4*rows), squeeze=False)
    fig.patch.set_facecolor("#1a1a2e")
    axes_flat = axes.flatten()
    
    task_infos = []
    for i, (key, is_parallel) in enumerate(tasks):
        ax = axes_flat[i]
        ax.set_facecolor("#16213e")
        
        if is_parallel:
            title, step_fn = PARALLEL_ALGORITHMS[key]
            steps = list(step_fn(list(data), workers=workers))
        else:
            title, step_fn = ALGORITHMS[key]
            steps = list(step_fn(list(data)))
            
        n = len(data)
        bars = ax.bar(range(n), data, color=DEFAULT_BAR_COLOUR, width=0.8)
        
        ax.set_xlim(-0.5, n - 0.5)
        ax.set_ylim(0, max(data) * 1.1)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        display_title = f"{title}" + (f" ({workers} workers)" if is_parallel else "")
        title_text = ax.set_title(display_title, color="white", fontsize=10)
        action_text = ax.text(0.5, 0.95, "", transform=ax.transAxes, 
                             ha="center", va="top", color="#bdc3c7", fontsize=8)
        
        task_infos.append({
            "steps": steps,
            "bars": bars,
            "title_text": title_text,
            "action_text": action_text,
            "total": len(steps),
            "done": False,
            "is_parallel": is_parallel,
            "display_title": display_title
        })
        
    for i in range(num_tasks, len(axes_flat)):
        axes_flat[i].axis('off')

    max_frames = max(info["total"] for info in task_infos)

    def update(frame_idx):
        for info in task_infos:
            step_idx = min(frame_idx, info["total"] - 1)
            arr, highlights, action = info["steps"][step_idx]
            
            if action == "done" or step_idx == info["total"] - 1:
                info["done"] = True

            base_action = action.split(':')[-1].strip()
            worker_id = None
            if info["is_parallel"] and "worker" in action:
                try:
                    worker_id = int(action.split('worker ')[1].split(':')[0])
                except: pass

            for i, bar in enumerate(info["bars"]):
                bar.set_height(arr[i])
                if info["done"]:
                    bar.set_color("#2ecc71")
                elif i in highlights:
                    if worker_id is not None:
                        colours = ["#3498db", "#e67e22", "#9b59b6", "#1abc9c", "#f39c12", "#d35400"]
                        bar.set_color(colours[worker_id % len(colours)])
                    else:
                        bar.set_color(ACTION_COLOURS.get(base_action, "#e74c3c"))
                else:
                    bar.set_color(DEFAULT_BAR_COLOUR)
            
            info["action_text"].set_text(f"Action: {action}")
            info["title_text"].set_text(f"{info['display_title']} — step {step_idx+1}/{info['total']}")
            
        return [bar for info in task_infos for bar in info["bars"]]

    anim = animation.FuncAnimation(
        fig, update, frames=max_frames, interval=DELAY_MS, blit=False, repeat=False
    )

    plt.tight_layout()
    if save_as:
        print(f"Saving visualization to {save_as}...")
        anim.save(save_as, writer="pillow", fps=1000 // DELAY_MS)
        plt.close(fig)
    else:
        plt.show()

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel Sorting Visualizer")
    parser.add_argument("--compare", nargs="*", help="Sequential algorithms to compare")
    parser.add_argument("--parallel", nargs="*", help="Parallel algorithms to compare")
    
    parser.add_argument("--workers", type=int, default=4, help="Number of workers for parallel visualization")
    parser.add_argument("--n", type=int, default=40, help="Number of elements")
    parser.add_argument("--save", action="store_true", help="Save as GIF")
    
    args = parser.parse_args()
    
    if not args.compare and not args.parallel:
        print("At least one of --compare or --parallel must be specified.")
        sys.exit(1)

    tasks = []
    if args.compare:
        for k in args.compare:
            if k.lower() in ALGORITHMS:
                tasks.append((k.lower(), False))
            else:
                print(f"Warning: Unknown sequential algorithm '{k}'")

    if args.parallel:
        for k in args.parallel:
            if k.lower() in PARALLEL_ALGORITHMS:
                tasks.append((k.lower(), True))
            else:
                print(f"Warning: Unknown parallel algorithm '{k}'")

    if not tasks:
        print("No valid algorithms specified.")
        sys.exit(1)

    random.seed(SEED)
    data = random.sample(range(1, args.n * 3), args.n)
    
    CHARTS_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), "charts")
    os.makedirs(CHARTS_DIR, exist_ok=True)

    save_path = None
    if args.save:
        name_parts = []
        if args.compare: name_parts.extend(args.compare)
        if args.parallel: name_parts.extend([f"p_{p}" for p in args.parallel])
        save_path = os.path.join(CHARTS_DIR, f"viz_{'_'.join(name_parts)}.gif")
        
    visualize_mixed(tasks, data, workers=args.workers, save_as=save_path)
