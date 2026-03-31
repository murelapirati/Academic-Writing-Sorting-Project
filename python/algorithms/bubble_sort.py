def bubble_sort(arr):
    """
    Bubble Sort
    -----------
    Repeatedly walks through the list comparing each pair of adjacent elements.
    If they are in the wrong order, swap them. After each full pass, the largest
    unseen element has "bubbled up" to its correct position at the end.

    The early-exit flag (`swapped`) is the key optimisation:
    - If a full pass produces zero swaps, the list is already sorted — stop early.
    - This makes the best case O(n) instead of O(n²).

    Complexity:
        Best case    O(n)    — already sorted (one pass, no swaps)
        Average case O(n²)   — random data
        Worst case   O(n²)   — reverse sorted (maximum swaps every pass)
        Space        O(1)    — sorts in-place, no extra memory
    """
    n = len(arr)

    for i in range(n - 1):
        # After i passes, the last i elements are already in their final position.
        # There is no need to look at them again.
        swapped = False

        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True

        # No swap in this pass → list is sorted, nothing left to do.
        if not swapped:
            break

    return arr
