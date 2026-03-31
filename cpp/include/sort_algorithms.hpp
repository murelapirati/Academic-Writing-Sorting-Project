#pragma once

#include <algorithm>
#include <cstddef>
#include <future>
#include <queue>
#include <utility>
#include <vector>

namespace sorting_cpp {

template <typename T>
void bubble_sort(std::vector<T>& arr) {
    const std::size_t n = arr.size();
    for (std::size_t i = 0; i + 1 < n; ++i) {
        bool swapped = false;
        for (std::size_t j = 0; j + 1 < n - i; ++j) {
            if (arr[j] > arr[j + 1]) {
                std::swap(arr[j], arr[j + 1]);
                swapped = true;
            }
        }
        if (!swapped) {
            break;
        }
    }
}

template <typename T>
void insertion_sort(std::vector<T>& arr) {
    for (std::size_t i = 1; i < arr.size(); ++i) {
        T key = arr[i];
        std::size_t j = i;
        while (j > 0 && arr[j - 1] > key) {
            arr[j] = arr[j - 1];
            --j;
        }
        arr[j] = std::move(key);
    }
}

template <typename T>
void merge_sort_impl(std::vector<T>& arr, std::vector<T>& tmp, std::size_t lo, std::size_t hi) {
    if (hi - lo <= 1) {
        return;
    }

    const std::size_t mid = lo + (hi - lo) / 2;
    merge_sort_impl(arr, tmp, lo, mid);
    merge_sort_impl(arr, tmp, mid, hi);

    std::size_t i = lo;
    std::size_t j = mid;
    std::size_t k = lo;

    while (i < mid && j < hi) {
        if (arr[i] <= arr[j]) {
            tmp[k++] = arr[i++];
        } else {
            tmp[k++] = arr[j++];
        }
    }
    while (i < mid) {
        tmp[k++] = arr[i++];
    }
    while (j < hi) {
        tmp[k++] = arr[j++];
    }
    for (std::size_t p = lo; p < hi; ++p) {
        arr[p] = std::move(tmp[p]);
    }
}

template <typename T>
void merge_sort(std::vector<T>& arr) {
    if (arr.size() < 2) {
        return;
    }
    std::vector<T> tmp(arr.size());
    merge_sort_impl(arr, tmp, 0, arr.size());
}

template <typename T>
std::size_t median_of_three(std::vector<T>& arr, std::size_t lo, std::size_t hi) {
    const std::size_t mid = lo + (hi - lo) / 2;
    if (arr[lo] > arr[mid]) {
        std::swap(arr[lo], arr[mid]);
    }
    if (arr[lo] > arr[hi]) {
        std::swap(arr[lo], arr[hi]);
    }
    if (arr[mid] > arr[hi]) {
        std::swap(arr[mid], arr[hi]);
    }
    return mid;
}

template <typename T>
void quick_sort_impl(std::vector<T>& arr, std::size_t lo, std::size_t hi) {
    if (lo >= hi) {
        return;
    }

    const std::size_t pivot_idx = median_of_three(arr, lo, hi);
    const T pivot = arr[pivot_idx];

    std::size_t lt = lo;
    std::size_t i = lo;
    std::size_t gt = hi;

    while (i <= gt) {
        if (arr[i] < pivot) {
            std::swap(arr[lt], arr[i]);
            ++lt;
            ++i;
        } else if (arr[i] > pivot) {
            std::swap(arr[i], arr[gt]);
            if (gt == 0) {
                break;
            }
            --gt;
        } else {
            ++i;
        }
    }

    if (lt > lo) {
        quick_sort_impl(arr, lo, lt - 1);
    }
    if (gt < hi) {
        quick_sort_impl(arr, gt + 1, hi);
    }
}

template <typename T>
void quick_sort(std::vector<T>& arr) {
    if (arr.size() < 2) {
        return;
    }
    quick_sort_impl(arr, 0, arr.size() - 1);
}

template <typename T>
std::vector<T> kway_merge(const std::vector<std::vector<T>>& chunks) {
    struct Node {
        T value;
        std::size_t chunk_idx;
        std::size_t item_idx;
    };

    struct Cmp {
        bool operator()(const Node& a, const Node& b) const {
            return b.value < a.value;
        }
    };

    std::priority_queue<Node, std::vector<Node>, Cmp> heap;
    std::size_t total = 0;

    for (std::size_t ci = 0; ci < chunks.size(); ++ci) {
        total += chunks[ci].size();
        if (!chunks[ci].empty()) {
            heap.push(Node{chunks[ci][0], ci, 0});
        }
    }

    std::vector<T> out;
    out.reserve(total);

    while (!heap.empty()) {
        const Node node = heap.top();
        heap.pop();
        out.push_back(node.value);

        const std::size_t next_idx = node.item_idx + 1;
        if (next_idx < chunks[node.chunk_idx].size()) {
            heap.push(Node{chunks[node.chunk_idx][next_idx], node.chunk_idx, next_idx});
        }
    }

    return out;
}

template <typename T, typename SortFn>
std::vector<T> parallel_chunk_sort(const std::vector<T>& input, std::size_t workers, SortFn sort_fn) {
    if (input.size() < 2 || workers <= 1) {
        std::vector<T> out = input;
        sort_fn(out);
        return out;
    }

    workers = std::max<std::size_t>(1, std::min<std::size_t>(workers, input.size()));
    const std::size_t chunk_size = (input.size() + workers - 1) / workers;

    std::vector<std::future<std::vector<T>>> futures;
    futures.reserve(workers);

    for (std::size_t start = 0; start < input.size(); start += chunk_size) {
        const std::size_t end = std::min<std::size_t>(start + chunk_size, input.size());
        futures.push_back(std::async(std::launch::async, [start, end, &input, sort_fn]() {
            std::vector<T> part(input.begin() + static_cast<std::ptrdiff_t>(start),
                                input.begin() + static_cast<std::ptrdiff_t>(end));
            sort_fn(part);
            return part;
        }));
    }

    std::vector<std::vector<T>> chunks;
    chunks.reserve(futures.size());
    for (auto& fut : futures) {
        chunks.push_back(fut.get());
    }

    return kway_merge(chunks);
}

}  // namespace sorting_cpp
