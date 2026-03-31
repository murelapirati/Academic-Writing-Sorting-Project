"""
parallel_insertion_sort.py
--------------------------
Process-parallel wrapper around insertion sort:
  1. Split the input list into chunks
  2. Insertion-sort each chunk in separate worker processes
  3. K-way merge sorted chunks

Like bubble sort, insertion sort is quadratic, so this is mainly for fair
algorithm-to-algorithm parallel benchmarking.
"""

import heapq
import multiprocessing
import os

from algorithms.insertion_sort import insertion_sort


def _sort_chunk(chunk):
    """Sort one chunk in a worker process."""
    return insertion_sort(list(chunk))


def parallel_insertion_sort(arr, workers=None):
    """Return a sorted copy of arr using process-parallel chunk sorting."""
    if workers is None:
        workers = os.cpu_count() or 1

    n = len(arr)
    if n < 512 or workers == 1:
        return insertion_sort(list(arr))

    chunk_size = (n + workers - 1) // workers
    chunks = [arr[i : i + chunk_size] for i in range(0, n, chunk_size)]

    with multiprocessing.Pool(processes=workers) as pool:
        sorted_chunks = pool.map(_sort_chunk, chunks, chunksize=1)

    return _kway_merge(sorted_chunks)


def _kway_merge(sorted_chunks):
    """Merge k sorted chunks into one sorted list."""
    result = []
    heap = []

    for ci, chunk in enumerate(sorted_chunks):
        if chunk:
            heapq.heappush(heap, (chunk[0], ci, 0))

    while heap:
        value, ci, ei = heapq.heappop(heap)
        result.append(value)

        next_ei = ei + 1
        if next_ei < len(sorted_chunks[ci]):
            heapq.heappush(heap, (sorted_chunks[ci][next_ei], ci, next_ei))

    return result
