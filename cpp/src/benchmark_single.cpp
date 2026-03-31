#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <vector>

#include "benchmark_utils.hpp"
#include "dataset.hpp"
#include "sort_algorithms.hpp"

namespace fs = std::filesystem;
using namespace sorting_cpp;

struct SingleRow {
    std::string algorithm;
    std::string dataset;
    std::size_t n{};
    long long wall_time_ns{};
    long long cpu_time_ns{};
    std::string status;
};

struct SingleStats {
    long long wall{};
    long long cpu{};
};

template <typename T>
SingleStats run_single_algorithm(const std::string& algorithm, std::vector<T>& arr) {
    auto measured = measure_sort_ns([&]() {
        if (algorithm == "bubble_sort") {
            bubble_sort(arr);
            return;
        }
        if (algorithm == "insertion_sort") {
            insertion_sort(arr);
            return;
        }
        if (algorithm == "merge_sort") {
            merge_sort(arr);
            return;
        }
        if (algorithm == "quick_sort") {
            quick_sort(arr);
            return;
        }
        throw std::runtime_error("Unknown single algorithm: " + algorithm);
    });

    return SingleStats{measured.first, measured.second};
}

SingleStats run_single_dispatch(const std::string& algorithm, const DataVariant& data) {
    return std::visit(
        [&](const auto& vec) -> SingleStats {
            using Vec = std::decay_t<decltype(vec)>;
            Vec copy = vec;
            return run_single_algorithm(algorithm, copy);
        },
        data);
}

int main() {
    const fs::path project_root = fs::path(__FILE__).parent_path().parent_path();
    const fs::path repo_root = project_root.parent_path();
    const fs::path cpp_data = project_root / "data";

    const fs::path index_file = cpp_data / "index.tsv";
    const fs::path csv_file = repo_root / "results_cpp_single.csv";
    const fs::path log_file = repo_root / "benchmark_cpp_log.txt";

    std::ofstream log(log_file);
    ensure_stream(log, log_file.string());

    auto emit = [&](const std::string& line = std::string()) {
        std::cout << line << '\n';
        log << line << '\n';
        log.flush();
    };

    const std::vector<std::string> algorithms = {
        "bubble_sort",
        "insertion_sort",
        "merge_sort",
        "quick_sort",
    };

    auto datasets = load_index_tsv(index_file.string());

    std::size_t max_n = 0;
    if (const char* env = std::getenv("SRT_MAX_N")) {
        max_n = static_cast<std::size_t>(std::stoull(env));
    }
    if (max_n > 0) {
        std::vector<DatasetMeta> filtered;
        filtered.reserve(datasets.size());
        for (const auto& ds : datasets) {
            if (ds.n <= max_n) {
                filtered.push_back(ds);
            }
        }
        datasets = std::move(filtered);
    }

    const std::size_t total = algorithms.size() * datasets.size();

    emit("C++ single benchmark");
    if (max_n > 0) {
        emit("Dataset filter: n <= " + std::to_string(max_n));
    }
    emit("Algorithms: 4");
    emit("Datasets: " + std::to_string(datasets.size()));
    emit("Total sorts: " + std::to_string(total));
    emit();

    emit("   #  algorithm         dataset                                         wall           cpu  status");
    emit("------------------------------------------------------------------------------------------------------");

    std::vector<SingleRow> rows;
    rows.reserve(total);

    std::size_t done = 0;

    for (const auto& meta : datasets) {
        const fs::path dataset_path = cpp_data / (meta.stem + ".bin");
        const DataVariant loaded = load_dataset_bin(dataset_path.string());

        for (const auto& algo : algorithms) {
            ++done;
            SingleRow row;
            row.algorithm = algo;
            row.dataset = meta.label;
            row.n = meta.n;

            try {
                const auto stats = run_single_dispatch(algo, loaded);
                row.wall_time_ns = stats.wall;
                row.cpu_time_ns = stats.cpu;
                row.status = "ok";

                std::ostringstream line;
                line << std::setw(4) << done << "  "
                     << std::left << std::setw(16) << algo
                     << std::left << std::setw(46) << meta.label
                     << std::right << std::setw(12) << fmt_time_ns(stats.wall) << "  "
                     << std::right << std::setw(12) << fmt_time_ns(stats.cpu) << "  "
                     << row.status;
                emit(line.str());
            } catch (const std::exception& ex) {
                row.wall_time_ns = 0;
                row.cpu_time_ns = 0;
                row.status = std::string("ERROR: ") + ex.what();

                std::ostringstream line;
                line << std::setw(4) << done << "  "
                     << std::left << std::setw(16) << algo
                     << std::left << std::setw(46) << meta.label
                     << std::right << std::setw(12) << "-" << "  "
                     << std::right << std::setw(12) << "-" << "  "
                     << row.status;
                emit(line.str());
            }

            rows.push_back(std::move(row));
        }
    }

    std::ofstream out(csv_file);
    ensure_stream(out, csv_file.string());
    out << "algorithm,dataset,n,wall_time_ns,cpu_time_ns,peak_memory_kb,status\n";
    for (const auto& row : rows) {
        out << row.algorithm << ','
            << '"' << row.dataset << '"' << ','
            << row.n << ','
            << (row.status == "ok" ? std::to_string(row.wall_time_ns) : "") << ','
            << (row.status == "ok" ? std::to_string(row.cpu_time_ns) : "") << ','
            << ','
            << '"' << row.status << '"'
            << '\n';
    }

    emit();
    emit("Done. Results saved to: " + csv_file.string());
    emit("Log saved to: " + log_file.string());

    return 0;
}
