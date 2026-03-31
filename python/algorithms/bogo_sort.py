import random
import time


def bogo_sort(arr, timeout_seconds=120):
    """
    Bogo Sort  (a.k.a. random sort, stupid sort, shotgun sort)
    ----------------------------------------------------------
    Repeatedly shuffle the list at random until it happens to be sorted.
    That's the entire algorithm.

    Why is this interesting?
        Unlike every other sorting algorithm, the speed of bogosort has nothing
        to do with the shape of the input (sorted, reversed, etc.) — only the
        SIZE of the list matters. Every run is pure chance.

        This means:
        - There is no "best case input" — a reverse-sorted list is just as likely
          to be solved in one shuffle as an already-sorted list fed in fresh.
        - The best case runtime is O(n)  — one shuffle, happens to be sorted.
        - The expected runtime is O(n × n!) — horrifyingly fast growth.
        - There is NO worst case — it could theoretically run forever.

    Expected shuffles by size:
        n=1  →            1   (always sorted already)
        n=2  →            2
        n=3  →            6
        n=4  →           24
        n=5  →          120
        n=6  →          720
        n=7  →        5,040
        n=8  →       40,320
        n=9  →      362,880
        n=10 →    3,628,800
        n=12 →  479,001,600   ← realistically never finishes in 2 minutes

    Returns:
        dict with keys:
            'sorted'   — the sorted list (or partially-shuffled if timeout hit)
            'shuffles' — number of shuffles attempted
            'time'     — wall-clock seconds elapsed
            'success'  — True if sorted within timeout, False if timeout hit
    """
    arr = list(arr)  # work on a copy

    shuffles = 0
    start = time.perf_counter()

    while not _is_sorted(arr):
        if time.perf_counter() - start >= timeout_seconds:
            return {
                "sorted": arr,
                "shuffles": shuffles,
                "time": time.perf_counter() - start,
                "success": False,
            }
        random.shuffle(arr)
        shuffles += 1

    return {
        "sorted": arr,
        "shuffles": shuffles,
        "time": time.perf_counter() - start,
        "success": True,
    }


def _is_sorted(arr):
    """Return True if arr is in non-decreasing order."""
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            return False
    return True
