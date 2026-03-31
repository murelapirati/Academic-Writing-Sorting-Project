"""
parallel_merge_sort.py
----------------------
A merge sort that distributes the sorting work across multiple CPU cores
using Python's multiprocessing module.

How it works:
    1. SPLIT   — divide the list into `workers` roughly equal chunks
    2. SORT    — sort each chunk in a separate process (true parallelism,
                 each process has its own GIL so they run simultaneously)
    3. MERGE   — k-way merge all sorted chunks back into one sorted list

Why only the sort phase is parallelised:
    The merge phase is inherently sequential — each merge step depends on the
    result of the previous one. This is Amdahl's Law in action:
    even with infinite cores, the sequential merge sets a floor on total time.

    At small n the process-spawn overhead dominates and parallel is SLOWER
    than single-core. The crossover point is part of what the benchmark reveals.

Worker counts to try: 1, 2, 4, 8, 16 (or os.cpu_count())
"""

import multiprocessing
import os
from algorithms.merge_sort import merge_sort


def _sort_chunk(chunk):
    """Sort a single chunk. Runs inside a worker process."""
    return merge_sort(list(chunk))


def parallel_merge_sort(arr, workers=None):
    """
    Sort `arr` using `workers` parallel processes.

    Parameters
    ----------
    arr     : list  — the input list (not mutated)
    workers : int   — number of worker processes; defaults to os.cpu_count()

    Returns
    -------
    Sorted list.
    """
    if workers is None:
        workers = os.cpu_count() or 1

    n = len(arr)

    # For very small inputs spawn overhead isn't worth it — sort directly.
    if n < 1024 or workers == 1:
        return merge_sort(list(arr))

    # ── 1. Split into chunks ───────────────────────────────────────────────────
    chunk_size = (n + workers - 1) // workers   # ceiling division
    chunks = [arr[i : i + chunk_size] for i in range(0, n, chunk_size)]

    # ── 2. Sort each chunk in a separate process ───────────────────────────────
    # Using a Pool so we don't have to manage process lifecycle manually.
    # chunksize=1 because our tasks are already large (sorting n/workers elements).
    with multiprocessing.Pool(processes=workers) as pool:
        sorted_chunks = pool.map(_sort_chunk, chunks, chunksize=1)

    # ── 3. K-way merge all sorted chunks ──────────────────────────────────────
    return _kway_merge(sorted_chunks)


def _kway_merge(sorted_chunks):
    """
    Merge k sorted lists into one sorted list using a min-heap.

    Naive approach — merge pairs repeatedly — is O(n log k) comparisons but
    does extra work. The heap approach is cleaner and equally O(n log k):
    maintain a heap of (value, chunk_index, position_in_chunk), always popping
    the smallest and refilling from that chunk.

    This is the same logic Python's heapq.merge() uses internally.
    """
    import heapq
    result = []

    # heap entry: (value, chunk_index, element_index)
    # We need chunk_index as a tiebreaker when values are equal and not
    # directly comparable across types (e.g. a tuple with a string).
    heap = []
    for ci, chunk in enumerate(sorted_chunks):
        if chunk:
            heapq.heappush(heap, (chunk[0], ci, 0))

    while heap:
        val, ci, ei = heapq.heappop(heap)
        result.append(val)
        next_ei = ei + 1
        if next_ei < len(sorted_chunks[ci]):
            heapq.heappush(heap, (sorted_chunks[ci][next_ei], ci, next_ei))

    return result
