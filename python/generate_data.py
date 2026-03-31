import pickle
import random
import string
import os
#BENCHMARKS MADE WITH AI!
# Where all benchmark files will be saved
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
DATA_DIR = os.path.join(REPO_ROOT, "data")

# ── Integer generators ─────────────────────────────────────────────────────────

def make_random_ints(n):
    """Uniformly random integers, no particular order."""
    return random.sample(range(n * 10), n)

def make_sorted_ints(n):
    """Already in ascending order — best case for insertion/bubble sort."""
    return list(range(n))

def make_reverse_ints(n):
    """Descending order — worst case for insertion/bubble sort."""
    return list(range(n, 0, -1))

def make_nearly_sorted_ints(n):
    """Sorted but with ~1% of elements randomly swapped — mimics real-world data."""
    data = list(range(n))
    num_swaps = max(1, n // 100)
    for _ in range(num_swaps):
        i, j = random.sample(range(n), 2)
        data[i], data[j] = data[j], data[i]
    return data

def make_duplicates_ints(n):
    """Heavy duplicates — only ~10 distinct values across n elements."""
    return [random.randint(0, 9) for _ in range(n)]


# ── String generators ──────────────────────────────────────────────────────────
# Strings are compared lexicographically in Python: 'Z' < 'a' because
# uppercase letters have lower ASCII values. This can produce surprising results.

def _random_word(min_len=3, max_len=10):
    """Generate a single random lowercase alphabetic word."""
    length = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_lowercase, k=length))

def make_random_strings(n):
    """Random lowercase words of varying length (3–10 chars)."""
    return [_random_word() for _ in range(n)]

def make_sorted_strings(n):
    """Pre-sorted list of random words — best case for insertion/bubble."""
    return sorted(_random_word() for _ in range(n))

def make_reverse_strings(n):
    """Reverse-sorted list of random words — worst case for insertion/bubble."""
    return sorted((_random_word() for _ in range(n)), reverse=True)

def make_nearly_sorted_strings(n):
    """Sorted words with ~1% randomly swapped."""
    data = sorted(_random_word() for _ in range(n))
    num_swaps = max(1, n // 100)
    for _ in range(num_swaps):
        i, j = random.sample(range(n), 2)
        data[i], data[j] = data[j], data[i]
    return data

def make_mixed_case_strings(n):
    """Mix of uppercase and lowercase words — exposes ASCII ordering surprises."""
    words = [_random_word() for _ in range(n)]
    # Randomly capitalise ~half of them
    return [w.capitalize() if random.random() < 0.5 else w for w in words]


# ── Tuple generators ───────────────────────────────────────────────────────────
# Tuples are compared element-by-element: (1, "b") > (1, "a").
# Here we use (int_score, str_name) pairs — like a leaderboard entry.
# Sorting these first ranks by score, then alphabetically by name on ties.

def make_random_tuples(n):
    """Random (score, name) pairs — both fields random."""
    return [(random.randint(0, 1000), _random_word()) for _ in range(n)]

def make_sorted_tuples(n):
    """Pre-sorted (score, name) pairs."""
    return sorted((random.randint(0, 1000), _random_word()) for _ in range(n))

def make_reverse_tuples(n):
    """Reverse-sorted (score, name) pairs."""
    return sorted(
        ((random.randint(0, 1000), _random_word()) for _ in range(n)),
        reverse=True,
    )

def make_nearly_sorted_tuples(n):
    """Sorted (score, name) pairs with ~1% randomly swapped."""
    data = sorted((random.randint(0, 1000), _random_word()) for _ in range(n))
    num_swaps = max(1, n // 100)
    for _ in range(num_swaps):
        i, j = random.sample(range(n), 2)
        data[i], data[j] = data[j], data[i]
    return data

def make_duplicate_score_tuples(n):
    """(score, name) where scores have heavy duplicates — tests tie-breaking."""
    return [(random.randint(0, 9), _random_word()) for _ in range(n)]


# ── Dataset table ──────────────────────────────────────────────────────────────
# Each row:  (filename_stem, label, n, generator)
#
# Integers  — random at all sizes; special cases at medium only (showcase)
# Strings   — random at all sizes; special cases at medium only
# Tuples    — random at all sizes; special cases at medium only

SIZES = {
    "tiny":   20,
    "small":  1_000,
    "medium": 10_000,
    "large":  100_000,
    "huge":   1_000_000,
}

def _expand(prefix, type_label, random_fn, sorted_fn, reverse_fn, nearly_fn, special_fn, special_label):
    """
    Generate a full row set for one data type:
    - random at all 5 sizes, with 5 trials each
    - sorted, reverse, nearly sorted, and a type-specific special case at all 5 sizes
    """
    rows = []
    TRIAL_COUNT = 5  # Number of random trials for more accurate benchmarking
    for size_name, n in SIZES.items():
        label_n = f"n={n:,}"
        
        # Multiple trials for 'Random' to ensure stats are robust
        for t in range(1, TRIAL_COUNT + 1):
            rows.append((f"{prefix}_random_{size_name}_t{t}", f"{type_label}: Random Trial {t} ({label_n})", n, random_fn))
            
        rows.append((f"{prefix}_sorted_{size_name}",  f"{type_label}: Sorted ({label_n})",        n, sorted_fn))
        rows.append((f"{prefix}_reverse_{size_name}", f"{type_label}: Reverse ({label_n})",       n, reverse_fn))
        rows.append((f"{prefix}_nearly_{size_name}",  f"{type_label}: Nearly Sorted ({label_n})", n, nearly_fn))
        rows.append((f"{prefix}_{special_label}_{size_name}", f"{type_label}: {special_label.replace('_', ' ').title()} ({label_n})", n, special_fn))
    return rows


DATASETS = (
    _expand("int", "Int",
            make_random_ints, make_sorted_ints, make_reverse_ints,
            make_nearly_sorted_ints, make_duplicates_ints, "duplicates")
    + _expand("str", "Str",
              make_random_strings, make_sorted_strings, make_reverse_strings,
              make_nearly_sorted_strings, make_mixed_case_strings, "mixed_case")
    + _expand("tup", "Tuple",
              make_random_tuples, make_sorted_tuples, make_reverse_tuples,
              make_nearly_sorted_tuples, make_duplicate_score_tuples, "dup_scores")
)

# ── Saving ─────────────────────────────────────────────────────────────────────

def save_dataset(filename_stem, label, n, generator):
    data = generator(n)
    payload = {
        "label": label,   # human-readable name used in benchmark results
        "n": n,
        "data": data,
    }
    path = os.path.join(DATA_DIR, f"{filename_stem}.pkl")
    with open(path, "wb") as f:
        pickle.dump(payload, f)
    print(f"  saved  {filename_stem}.pkl  ({n:,} elements)")


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Generating {len(DATASETS)} benchmark datasets into '{DATA_DIR}' ...\n")
    for args in DATASETS:
        save_dataset(*args)
    print("\nDone. Run benchmark.py next.")
