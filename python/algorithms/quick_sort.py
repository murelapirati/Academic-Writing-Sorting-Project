def quick_sort(arr):
    """
    Quick Sort
    ----------
    Divide-and-conquer like merge sort, but splits by VALUE instead of position.

    Pick a pivot element, then PARTITION the list into:
        - everything less than the pivot  (left)
        - everything equal to the pivot   (middle)
        - everything greater than pivot   (right)
    Then recursively sort left and right (middle is already in place by definition).

    Pivot strategy — median-of-three:
        Look at the first, middle, and last elements; pick the middle value.
        This avoids the classic O(n²) worst case that a "always pick first element"
        strategy hits on already-sorted input.

    Why is the worst case still O(n²)?
        If the pivot is always the smallest or largest element (bad luck, or adversarial
        input after pivot exposure), every partition produces one empty side and one
        side of n-1 elements — n levels deep instead of log n. With median-of-three
        this is rare on random data but can still be triggered on certain patterns.

    Complexity:
        Best case    O(n log n)  — balanced partitions every time
        Average case O(n log n)  — expected on random data
        Worst case   O(n²)       — maximally unbalanced partitions every time
        Space        O(log n)    — recursion stack (O(n) worst case)
    """
    _quick_sort(arr, 0, len(arr) - 1)
    return arr


def _median_of_three(arr, lo, hi):
    """
    Return the index of the median of arr[lo], arr[mid], arr[hi].
    Using the median as pivot keeps partitions balanced on sorted/reverse input.
    """
    mid = (lo + hi) // 2
    # Sort lo, mid, hi so arr[mid] ends up as the median value.
    if arr[lo] > arr[mid]:
        arr[lo], arr[mid] = arr[mid], arr[lo]
    if arr[lo] > arr[hi]:
        arr[lo], arr[hi] = arr[hi], arr[lo]
    if arr[mid] > arr[hi]:
        arr[mid], arr[hi] = arr[hi], arr[mid]
    # arr[lo] ≤ arr[mid] ≤ arr[hi] — median is at mid
    return mid


def _quick_sort(arr, lo, hi):
    if lo >= hi:
        return  # base case: 0 or 1 element, already sorted

    pivot_idx = _median_of_three(arr, lo, hi)
    pivot = arr[pivot_idx]

    # Three-way partition (Dijkstra's "Dutch National Flag"):
    # Handles duplicates efficiently — equal elements cluster in the middle
    # and are never recursed into again.
    #
    #  arr[lo .. lt-1]  <  pivot
    #  arr[lt .. gt]    == pivot
    #  arr[gt+1 .. hi]  >  pivot
    lt = lo   # left boundary of "equal" region
    gt = hi   # right boundary of "equal" region
    i  = lo   # current element being examined

    while i <= gt:
        if arr[i] < pivot:
            arr[lt], arr[i] = arr[i], arr[lt]
            lt += 1
            i += 1
        elif arr[i] > pivot:
            arr[i], arr[gt] = arr[gt], arr[i]
            gt -= 1
            # don't increment i — the swapped element hasn't been examined yet
        else:
            i += 1  # arr[i] == pivot, already in the right region

    # Recursively sort the < and > regions; the == region needs no further work.
    _quick_sort(arr, lo, lt - 1)
    _quick_sort(arr, gt + 1, hi)
