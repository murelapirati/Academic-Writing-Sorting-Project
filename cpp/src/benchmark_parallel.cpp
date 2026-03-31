#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include "benchmark_utils.hpp"
#include "dataset.hpp"
#include "sort_algorithms.hpp"

namespace fs = std::filesystem;
using namespace sorting_cpp;

struct ParallelRow {
    std::string algorithm;
    std::size_t workers{};
    std::string dataset;
    std::size_t n{};
    long long wall_time_ns{};
    double speedup{};
    double efficiency{};
    std::string status;
};

template <typename T>
long long run_parallel_algorithm(const std::string& algorithm, const std::vector<T>& arr, std::size_t workers) {
    auto measured = measure_sort_ns([&]() {
        std::vector<T> sorted;

        if (algorithm == "parallel_merge_sort") {
            sorted = parallel_chunk_sort(arr, workers, [](std::vector<T>& v) { merge_sort(v); });
        } else if (algorithm == "parallel_quick_sort") {
            sorted = parallel_chunk_sort(arr, workers, [](std::vector<T>& v) { quick_sort(v); });
        } else if (algorithm == "parallel_bubble_sort") {
            sorted = parallel_chunk_sort(arr, workers, [](std::vector<T>& v) { bubble_sort(v); });
        } else if (algorithm == "parallel_insertion_sort") {
            sorted = parallel_chunk_sort(arr, workers, [](std::vector<T>& v) { insertion_sort(v); });
        } else {
            throw std::runtime_error("Unknown parallel algorithm: " + algorithm);
        }

        (void)sorted;
    });

    return measured.first;
}

long long run_parallel_dispatch(const std::string& algorithm, const DataVariant& data, std::size_t workers) {
    return std::visit(
        [&](const auto& vec) -> long long {
            return run_parallel_algorithm(algorithm, vec, workers);
        },
        data);
}

int main() {
    const fs::path project_root = fs::path(__FILE__).parent_path().parent_path();
    const fs::path repo_root = project_root.parent_path();
    const fs::path cpp_data = project_root / "data";

    const fs::path index_file = cpp_data / "index.tsv";
    const fs::path csv_file = repo_root / "results_cpp_parallel.csv";
    const fs::path log_file = repo_root / "benchmark_cpp_parallel_log.txt";

    std::ofstream log(log_file);
    ensure_stream(log, log_file.string());

    auto emit = [&](const std::string& line = std::string()) {
        std::cout << line << '\n';
        log << line << '\n';
        log.flush();
    };

    const std::vector<std::string> algorithms = {
        "parallel_merge_sort",
        "parallel_quick_sort",
        "parallel_bubble_sort",
        "parallel_insertion_sort",
    };

    const std::size_t max_cpus = std::max(1u, std::thread::hardware_concurrency());
    std::vector<std::size_t> worker_counts;
    for (std::size_t w : {4u, 8u, 16u}) {
        if (w <= max_cpus * 2) {
            worker_counts.push_back(w);
        }
    }
    if (worker_counts.empty()) {
        worker_counts.push_back(1);
    }

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

    const std::size_t total_jobs = algorithms.size() * datasets.size() * worker_counts.size();

    emit("C++ parallel benchmark");
    if (max_n > 0) {
        emit("Dataset filter: n <= " + std::to_string(max_n));
    }
    emit("Machine CPU count: " + std::to_string(max_cpus));

    std::ostringstream workers_line;
    workers_line << "Worker counts: [";
    for (std::size_t i = 0; i < worker_counts.size(); ++i) {
        if (i) {
            workers_line << ", ";
        }
        workers_line << worker_counts[i];
    }
    workers_line << "]";
    emit(workers_line.str());

    emit("Algorithms: 4");
    emit("Datasets: " + std::to_string(datasets.size()));
    emit("Total jobs: " + std::to_string(total_jobs));
    emit();

    emit("algorithm                  workers  dataset                                         wall       speedup  efficiency  status");
    emit("----------------------------------------------------------------------------------------------------------------------------");

    std::vector<ParallelRow> rows;
    rows.reserve(total_jobs);

    for (const auto& algo : algorithms) {
        emit("[" + algo + "] datasets: " + std::to_string(datasets.size()));

        for (const auto& meta : datasets) {
            const fs::path dataset_path = cpp_data / (meta.stem + ".bin");
            const DataVariant loaded = load_dataset_bin(dataset_path.string());

            long long baseline_ns = 0;

            for (std::size_t w : worker_counts) {
                ParallelRow row;
                row.algorithm = algo;
                row.workers = w;
                row.dataset = meta.label;
                row.n = meta.n;

                try {
                    const auto wall_ns = run_parallel_dispatch(algo, loaded, w);
                    row.wall_time_ns = wall_ns;
                    row.status = "ok";

                    if (w == worker_counts.front()) {
                        baseline_ns = wall_ns;
                    }

                    if (baseline_ns > 0 && wall_ns > 0) {
                        row.speedup = static_cast<double>(baseline_ns) / static_cast<double>(wall_ns);
                        row.efficiency = row.speedup / static_cast<double>(w);
                    }

                    std::ostringstream line;
                    line << std::left << std::setw(25) << algo
                         << std::right << std::setw(7) << w << "  "
                         << std::left << std::setw(46) << meta.label
                         << std::right << std::setw(12) << fmt_time_ns(wall_ns) << "  "
                         << std::setw(8) << std::fixed << std::setprecision(3) << row.speedup << "  "
                         << std::setw(10) << std::fixed << std::setprecision(3) << row.efficiency << "  "
                         << row.status;
                    emit(line.str());
                } catch (const std::exception& ex) {
                    row.status = std::string("ERROR: ") + ex.what();

                    std::ostringstream line;
                    line << std::left << std::setw(25) << algo
                         << std::right << std::setw(7) << w << "  "
                         << std::left << std::setw(46) << meta.label
                         << std::right << std::setw(12) << "-" << "  "
                         << std::setw(8) << "-" << "  "
                         << std::setw(10) << "-" << "  "
                         << row.status;
                    emit(line.str());
                }

                rows.push_back(std::move(row));
            }

            emit();
        }
    }

    std::ofstream out(csv_file);
    ensure_stream(out, csv_file.string());
    out << "algorithm,workers,dataset,n,wall_time_ns,speedup,efficiency,status\n";
    for (const auto& row : rows) {
        out << row.algorithm << ','
            << row.workers << ','
            << '"' << row.dataset << '"' << ','
            << row.n << ','
            << (row.status == "ok" ? std::to_string(row.wall_time_ns) : "") << ','
            << (row.status == "ok" ? std::to_string(row.speedup) : "") << ','
            << (row.status == "ok" ? std::to_string(row.efficiency) : "") << ','
            << '"' << row.status << '"'
            << '\n';
    }

    emit("Results saved to: " + csv_file.string());
    emit("Log saved to: " + log_file.string());

    return 0;
}
