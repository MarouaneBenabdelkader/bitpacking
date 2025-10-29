"""Benchmark harness for bit packing implementations.

Uses time.perf_counter_ns for high-resolution timing.
Reports median and p95 latencies in nanoseconds.
Outputs JSON lines for easy parsing.
"""

import json
import random
import time

from bitpacking.factory import get_bitpacking


def percentile(data: list[float], p: float) -> float:
    """Calculate percentile of sorted data."""
    if not data:
        return 0.0
    data = sorted(data)
    k = (len(data) - 1) * p
    f = int(k)
    c = f + 1
    if c >= len(data):
        return data[-1]
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return d0 + d1


def benchmark_compress(bp, data: list[int], warmup: int = 3, repeats: int = 10) -> dict:
    """Benchmark compress operation."""
    # Warmup
    for _ in range(warmup):
        bp.compress(data)

    # Measure
    timings = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        bp.compress(data)
        end = time.perf_counter_ns()
        timings.append(end - start)

    return {"median_ns": percentile(timings, 0.5), "p95_ns": percentile(timings, 0.95)}


def benchmark_get(bp, n: int, warmup: int = 3, repeats: int = 10) -> dict:
    """Benchmark random get operations."""
    indices = [random.randint(0, n - 1) for _ in range(10000)]

    # Warmup
    for _ in range(warmup):
        for i in indices[:100]:
            bp.get(i)

    # Measure
    timings = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        for i in indices:
            bp.get(i)
        end = time.perf_counter_ns()
        timings.append((end - start) / len(indices))

    return {"median_ns": percentile(timings, 0.5), "p95_ns": percentile(timings, 0.95)}


def benchmark_decompress(bp, pack: dict, warmup: int = 3, repeats: int = 10) -> dict:
    """Benchmark decompress operation."""
    # Warmup
    for _ in range(warmup):
        bp.decompress(pack)

    # Measure
    timings = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        bp.decompress(pack)
        end = time.perf_counter_ns()
        timings.append(end - start)

    return {"median_ns": percentile(timings, 0.5), "p95_ns": percentile(timings, 0.95)}


def run_benchmarks(implementation: str = "noncross"):
    """
    Run all benchmarks and print JSON results.

    Args:
        implementation: Name of implementation to benchmark ("noncross" or "cross")
    """
    bp = get_bitpacking(implementation)

    # Dataset 1: Small values (0-255)
    small_data = [random.randint(0, 255) for _ in range(10000)]
    pack_small = bp.compress(small_data)
    k_small = pack_small["k"]

    results = benchmark_compress(bp, small_data)
    print(
        json.dumps(
            {
                "case": "small",
                "impl": implementation,
                "n": len(small_data),
                "k": k_small,
                "op": "compress",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    results = benchmark_get(bp, len(small_data))
    print(
        json.dumps(
            {
                "case": "small",
                "impl": implementation,
                "n": len(small_data),
                "k": k_small,
                "op": "get",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    results = benchmark_decompress(bp, pack_small)
    print(
        json.dumps(
            {
                "case": "small",
                "impl": implementation,
                "n": len(small_data),
                "k": k_small,
                "op": "decompress",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    # Dataset 2: Medium values (0-65535)
    medium_data = [random.randint(0, 65535) for _ in range(10000)]
    pack_medium = bp.compress(medium_data)
    k_medium = pack_medium["k"]

    results = benchmark_compress(bp, medium_data)
    print(
        json.dumps(
            {
                "case": "medium",
                "impl": implementation,
                "n": len(medium_data),
                "k": k_medium,
                "op": "compress",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    results = benchmark_get(bp, len(medium_data))
    print(
        json.dumps(
            {
                "case": "medium",
                "impl": implementation,
                "n": len(medium_data),
                "k": k_medium,
                "op": "get",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    results = benchmark_decompress(bp, pack_medium)
    print(
        json.dumps(
            {
                "case": "medium",
                "impl": implementation,
                "n": len(medium_data),
                "k": k_medium,
                "op": "decompress",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    # Dataset 3: Skewed (mostly small, few large)
    skewed_data = [random.randint(0, 10) for _ in range(9900)] + [
        random.randint(10000, 100000) for _ in range(100)
    ]
    random.shuffle(skewed_data)
    pack_skewed = bp.compress(skewed_data)
    k_skewed = pack_skewed["k"]

    results = benchmark_compress(bp, skewed_data)
    print(
        json.dumps(
            {
                "case": "skewed",
                "impl": implementation,
                "n": len(skewed_data),
                "k": k_skewed,
                "op": "compress",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    results = benchmark_get(bp, len(skewed_data))
    print(
        json.dumps(
            {
                "case": "skewed",
                "impl": implementation,
                "n": len(skewed_data),
                "k": k_skewed,
                "op": "get",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )

    results = benchmark_decompress(bp, pack_skewed)
    print(
        json.dumps(
            {
                "case": "skewed",
                "impl": implementation,
                "n": len(skewed_data),
                "k": k_skewed,
                "op": "decompress",
                "median_ns": int(results["median_ns"]),
                "p95_ns": int(results["p95_ns"]),
            }
        )
    )


if __name__ == "__main__":
    run_benchmarks()
