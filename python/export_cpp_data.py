"""
export_cpp_data.py
------------------
Converts Python benchmark datasets from data/*.pkl into a C++ friendly binary format.

This keeps Python and C++ benchmarks on identical dataset contents.

Output:
    cpp/data/index.tsv
    cpp/data/*.bin
"""

import os
import pickle
import struct

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
PY_DATA_DIR = os.path.join(REPO_ROOT, "data")
CPP_DATA_DIR = os.path.join(REPO_ROOT, "cpp", "data")
INDEX_PATH = os.path.join(CPP_DATA_DIR, "index.tsv")

TYPE_INT = "int"
TYPE_STR = "str"
TYPE_TUP = "tuple"

TYPE_TO_CODE = {
    TYPE_INT: 0,
    TYPE_STR: 1,
    TYPE_TUP: 2,
}


def detect_type(items):
    if not items:
        return TYPE_INT

    first = items[0]
    if isinstance(first, int):
        return TYPE_INT
    if isinstance(first, str):
        return TYPE_STR
    if isinstance(first, tuple) and len(first) == 2 and isinstance(first[0], int) and isinstance(first[1], str):
        return TYPE_TUP

    raise TypeError(f"Unsupported dataset element type: {type(first)!r}")


def write_bin(path, kind, items):
    with open(path, "wb") as f:
        # Header: magic + version + type + count
        f.write(b"SRTBIN1")
        f.write(struct.pack("<B", TYPE_TO_CODE[kind]))
        f.write(struct.pack("<Q", len(items)))

        if kind == TYPE_INT:
            for value in items:
                f.write(struct.pack("<q", int(value)))
            return

        if kind == TYPE_STR:
            for value in items:
                encoded = value.encode("utf-8")
                f.write(struct.pack("<I", len(encoded)))
                f.write(encoded)
            return

        for score, name in items:
            encoded = name.encode("utf-8")
            f.write(struct.pack("<qI", int(score), len(encoded)))
            f.write(encoded)


if __name__ == "__main__":
    os.makedirs(CPP_DATA_DIR, exist_ok=True)

    rows = []
    for fname in sorted(os.listdir(PY_DATA_DIR)):
        if not fname.endswith(".pkl"):
            continue

        stem = fname[:-4]
        pkl_path = os.path.join(PY_DATA_DIR, fname)

        with open(pkl_path, "rb") as f:
            payload = pickle.load(f)

        label = payload["label"]
        n = int(payload["n"])
        data = payload["data"]

        kind = detect_type(data)
        out_path = os.path.join(CPP_DATA_DIR, f"{stem}.bin")
        write_bin(out_path, kind, data)

        rows.append((stem, label, str(n), kind))
        print(f"saved {stem}.bin ({kind}, n={n:,})")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write("stem\tlabel\tn\ttype\n")
        for row in rows:
            # labels contain commas; TSV avoids CSV quoting complexity
            f.write("\t".join(row) + "\n")

    print(f"\nDone. Wrote {len(rows)} datasets to {CPP_DATA_DIR}")
    print(f"Index file: {INDEX_PATH}")
