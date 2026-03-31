import sys

# Python's default recursion limit is 1000.
# Merge sort on a list of n elements recurses to depth log₂(n).
# For n = 1,000,000 that's ~20 levels — well within even the default limit.
# We raise it slightly as a safety margin for any edge cases.
sys.setrecursionlimit(10_000)


def merge_sort(arr):
    """
    Merge Sort
    ----------
    A divide-and-conquer algorithm:
        1. DIVIDE   — split the list in half
        2. CONQUER  — recursively sort each half
        3. COMBINE  — merge the two sorted halves into one sorted list

    The merge step is the heart of the algorithm:
        left  = [1, 3, 5]
        right = [2, 4, 6]
        Compare fronts: 1 < 2 → take 1   result = [1]
        Compare fronts: 3 > 2 → take 2   result = [1, 2]
        Compare fronts: 3 < 4 → take 3   result = [1, 2, 3]
        ... and so on until one side is exhausted, then append the rest.

    Why is it always O(n log n)?
        - There are log₂(n) levels of splitting.
        - At each level, the merge step touches every element exactly once → O(n).
        - Total: O(n) × O(log n) = O(n log n), regardless of input order.

    The trade-off: it needs O(n) extra memory for the temporary left/right arrays
    created during each merge — unlike bubble/insertion which sort in-place.

    Complexity:
        Best case    O(n log n)  — always
        Average case O(n log n)  — always
        Worst case   O(n log n)  — always (input order doesn't matter)
        Space        O(n)        — extra memory for merge buffers
    """
    if len(arr) <= 1:
        # Base case: a list of 0 or 1 elements is already sorted.
        return arr

    mid = len(arr) // 2
    left  = merge_sort(arr[:mid])   # recursively sort left half
    right = merge_sort(arr[mid:])   # recursively sort right half

    return _merge(left, right)


def _merge(left, right):
    """
    Merge two already-sorted lists into one sorted list.
    This is a helper and is not meant to be called directly.
    """
    result = []
    i = j = 0

    # Pick the smaller front element from either side until one is exhausted.
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # One side is empty — append whatever remains in the other (already sorted).
    result.extend(left[i:])
    result.extend(right[j:])

    return result
