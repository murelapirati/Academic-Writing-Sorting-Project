#pragma once

#include <cstdint>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <variant>
#include <vector>

namespace sorting_cpp {

struct TupleItem {
    std::int64_t score{};
    std::string name;

    bool operator<(const TupleItem& other) const {
        return std::tie(score, name) < std::tie(other.score, other.name);
    }

    bool operator>(const TupleItem& other) const {
        return other < *this;
    }

    bool operator<=(const TupleItem& other) const {
        return !(other < *this);
    }
};

enum class DataType {
    Int,
    Str,
    Tuple,
};

struct DatasetMeta {
    std::string stem;
    std::string label;
    std::size_t n{};
    DataType type{DataType::Int};
};

using IntVec = std::vector<std::int64_t>;
using StrVec = std::vector<std::string>;
using TupVec = std::vector<TupleItem>;
using DataVariant = std::variant<IntVec, StrVec, TupVec>;

inline DataType parse_data_type(const std::string& s) {
    if (s == "int") {
        return DataType::Int;
    }
    if (s == "str") {
        return DataType::Str;
    }
    if (s == "tuple") {
        return DataType::Tuple;
    }
    throw std::runtime_error("Unknown data type: " + s);
}

inline std::vector<DatasetMeta> load_index_tsv(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("Failed to open index file: " + path);
    }

    std::vector<DatasetMeta> metas;
    std::string line;

    if (!std::getline(in, line)) {
        return metas;
    }

    while (std::getline(in, line)) {
        if (line.empty()) {
            continue;
        }

        std::stringstream ss(line);
        std::string stem;
        std::string label;
        std::string n_str;
        std::string type_str;

        if (!std::getline(ss, stem, '\t') ||
            !std::getline(ss, label, '\t') ||
            !std::getline(ss, n_str, '\t') ||
            !std::getline(ss, type_str, '\t')) {
            throw std::runtime_error("Malformed index row: " + line);
        }

        DatasetMeta meta;
        meta.stem = stem;
        meta.label = label;
        meta.n = static_cast<std::size_t>(std::stoull(n_str));
        meta.type = parse_data_type(type_str);
        metas.push_back(std::move(meta));
    }

    return metas;
}

template <typename T>
inline T read_scalar(std::ifstream& in) {
    T value{};
    in.read(reinterpret_cast<char*>(&value), sizeof(T));
    if (!in) {
        throw std::runtime_error("Unexpected EOF while reading binary dataset");
    }
    return value;
}

inline std::string read_string(std::ifstream& in) {
    const auto len = read_scalar<std::uint32_t>(in);
    std::string out;
    out.resize(len);
    if (len > 0) {
        in.read(out.data(), static_cast<std::streamsize>(len));
        if (!in) {
            throw std::runtime_error("Unexpected EOF while reading string payload");
        }
    }
    return out;
}

inline DataVariant load_dataset_bin(const std::string& bin_path) {
    std::ifstream in(bin_path, std::ios::binary);
    if (!in) {
        throw std::runtime_error("Failed to open binary dataset: " + bin_path);
    }

    char magic[7]{};
    in.read(magic, 7);
    if (!in || std::string(magic, 7) != "SRTBIN1") {
        throw std::runtime_error("Invalid dataset magic for file: " + bin_path);
    }

    const auto type_code = read_scalar<std::uint8_t>(in);
    const auto count = read_scalar<std::uint64_t>(in);

    if (type_code == 0) {
        IntVec v;
        v.reserve(static_cast<std::size_t>(count));
        for (std::uint64_t i = 0; i < count; ++i) {
            v.push_back(read_scalar<std::int64_t>(in));
        }
        return v;
    }

    if (type_code == 1) {
        StrVec v;
        v.reserve(static_cast<std::size_t>(count));
        for (std::uint64_t i = 0; i < count; ++i) {
            v.push_back(read_string(in));
        }
        return v;
    }

    if (type_code == 2) {
        TupVec v;
        v.reserve(static_cast<std::size_t>(count));
        for (std::uint64_t i = 0; i < count; ++i) {
            TupleItem item;
            item.score = read_scalar<std::int64_t>(in);
            item.name = read_string(in);
            v.push_back(std::move(item));
        }
        return v;
    }

    throw std::runtime_error("Unsupported dataset type code in file: " + bin_path);
}

}  // namespace sorting_cpp
