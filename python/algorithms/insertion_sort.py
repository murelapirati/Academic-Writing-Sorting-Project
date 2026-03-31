def insertion_sort(arr):
    """
    Insertion Sort
    --------------
    Maintains a sorted "left portion" of the list, growing it one element at a time.
    For each new element (the "key"), slide it leftward through the sorted portion
    until it finds its correct position — exactly like sorting a hand of playing cards.

    How a single step works:
        sorted part  |  unsorted part
        [1, 3, 5]    |  [2, 8, 4, ...]
                          ^
                          key = 2
        Compare 2 with 5 → 5 > 2, shift 5 right
        Compare 2 with 3 → 3 > 2, shift 3 right
        Compare 2 with 1 → 1 < 2, stop
        Insert 2 here → [1, 2, 3, 5]

    The inner while loop shifts elements right (instead of swapping), which is
    faster than swap-based variants — one write per step instead of three.

    Complexity:
        Best case    O(n)    — already sorted (inner loop never executes)
        Average case O(n²)   — random data
        Worst case   O(n²)   — reverse sorted (key slides all the way to index 0)
        Space        O(1)    — in-place
    """
    for i in range(1, len(arr)):
        key = arr[i]   # the element we are about to place correctly

        j = i - 1
        # Shift elements of the sorted portion that are greater than key
        # one position to the right, making room for key.
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1

        # j+1 is now the correct slot for key.
        arr[j + 1] = key

    return arr
