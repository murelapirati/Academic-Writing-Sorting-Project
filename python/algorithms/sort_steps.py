"""
sort_steps.py
-------------
Generator versions of each sorting algorithm.

Instead of sorting silently, each function yields the array state
after every meaningful step (comparison or swap), along with the
indices being examined. This powers the visualizer.

Each generator yields:  (array_snapshot, highlight_indices, action_label)
  - array_snapshot   : copy of the array at this moment
  - highlight_indices: list of indices to colour (e.g. the two being compared)
  - action_label     : short string like "compare", "swap", "insert"
"""


def bubble_sort_steps(arr):
    arr = list(arr)
    n = len(arr)

    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            yield list(arr), [j, j + 1], "compare"
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
                yield list(arr), [j, j + 1], "swap"
        if not swapped:
            break

    yield list(arr), [], "done"


def insertion_sort_steps(arr):
    arr = list(arr)

    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        yield list(arr), [i], "pick key"

        while j >= 0 and arr[j] > key:
            yield list(arr), [j, j + 1], "compare"
            arr[j + 1] = arr[j]
            j -= 1
            yield list(arr), [j + 1], "shift"

        arr[j + 1] = key
        yield list(arr), [j + 1], "insert"

    yield list(arr), [], "done"


def merge_sort_steps(arr):
    arr = list(arr)
    steps = []
    _merge_sort_collect(arr, 0, len(arr) - 1, steps)
    yield from steps
    yield list(arr), [], "done"


def _merge_sort_collect(arr, lo, hi, steps):
    if lo >= hi:
        return
    mid = (lo + hi) // 2
    _merge_sort_collect(arr, lo, mid, steps)
    _merge_sort_collect(arr, mid + 1, hi, steps)
    _merge_inplace(arr, lo, mid, hi, steps)


def _merge_inplace(arr, lo, mid, hi, steps):
    left  = arr[lo : mid + 1]
    right = arr[mid + 1 : hi + 1]
    i = j = 0
    k = lo
    while i < len(left) and j < len(right):
        steps.append((list(arr), [lo + i, mid + 1 + j], "compare"))
        if left[i] <= right[j]:
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        steps.append((list(arr), [k], "place"))
        k += 1
    while i < len(left):
        arr[k] = left[i]
        steps.append((list(arr), [k], "place"))
        i += 1; k += 1
    while j < len(right):
        arr[k] = right[j]
        steps.append((list(arr), [k], "place"))
        j += 1; k += 1


def quick_sort_steps(arr):
    arr = list(arr)
    steps = []
    _quick_collect(arr, 0, len(arr) - 1, steps)
    yield from steps
    yield list(arr), [], "done"


def _quick_collect(arr, lo, hi, steps):
    if lo >= hi:
        return
    lt, gt = _partition_collect(arr, lo, hi, steps)
    _quick_collect(arr, lo, lt - 1, steps)
    _quick_collect(arr, gt + 1, hi, steps)


def _partition_collect(arr, lo, hi, steps):
    # Median-of-three pivot
    mid = (lo + hi) // 2
    if arr[lo] > arr[mid]: arr[lo], arr[mid] = arr[mid], arr[lo]
    if arr[lo] > arr[hi]:  arr[lo], arr[hi]  = arr[hi],  arr[lo]
    if arr[mid] > arr[hi]: arr[mid], arr[hi] = arr[hi],  arr[mid]
    pivot = arr[mid]

    lt, gt, i = lo, hi, lo
    while i <= gt:
        steps.append((list(arr), [i, lt, gt], "compare"))
        if arr[i] < pivot:
            arr[lt], arr[i] = arr[i], arr[lt]
            steps.append((list(arr), [lt, i], "swap"))
            lt += 1; i += 1
        elif arr[i] > pivot:
            arr[i], arr[gt] = arr[gt], arr[i]
            steps.append((list(arr), [i, gt], "swap"))
            gt -= 1
        else:
            i += 1
def parallel_merge_sort_steps(arr, workers=4):
    """
    Yields steps for a parallel-style merge sort (chunked).
    Shows the array being split, sorted independently, then k-way merged.
    """
    arr = list(arr)
    n = len(arr)
    chunk_size = (n + workers - 1) // workers
    
    # 1. Split into chunks (highlight boundaries)
    chunk_indices = [i for i in range(0, n, chunk_size)]
    yield list(arr), chunk_indices, "split"

    # 2. Sort each chunk (simulate sequential sorting of each chunk for animation)
    # In a real parallel merge sort, these happen at the same time.
    # To visualize "parallelism", we can interleave steps or just show them in order.
    # For a simple animator, we'll sort them sequentially but label them as worker tasks.
    for w in range(workers):
        lo = w * chunk_size
        hi = min((w + 1) * chunk_size - 1, n - 1)
        if lo > hi: break
        
        # We'll use merge sort for each chunk
        chunk_steps = []
        _merge_sort_collect(arr, lo, hi, chunk_steps)
        for state, highlights, action in chunk_steps:
            yield state, highlights, f"worker {w}: {action}"

    # 3. K-way merge
    import heapq
    sorted_chunks = []
    for w in range(workers):
        lo = w * chunk_size
        hi = min((w + 1) * chunk_size, n)
        if lo >= n: break
        sorted_chunks.append(arr[lo:hi])

    result = []
    heap = []
    for ci, chunk in enumerate(sorted_chunks):
        if chunk:
            heapq.heappush(heap, (chunk[0], ci, 0))

    while heap:
        val, ci, ei = heapq.heappop(heap)
        
        # Calculate original index for highlighting
        # This is tricky because the 'result' is being built separately.
        # For visualization, we'll just show the element being 'picked' from its chunk.
        orig_idx = ci * chunk_size + ei
        yield list(arr), [orig_idx], "k-way merge: pick"
        
        result.append(val)
        # Update the visual array to show the element being moved to the front (pseudo-merge)
        # In a real inplace merge it's different, but for visualization we'll just show progress.
        
        next_ei = ei + 1
        if next_ei < len(sorted_chunks[ci]):
            heapq.heappush(heap, (sorted_chunks[ci][next_ei], ci, next_ei))

    # Final sorted state
    yield sorted(arr), [], "done"
