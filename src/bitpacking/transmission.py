"""Transmission time analysis for bit packing.

This module provides utilities to calculate when compression is beneficial
given network bandwidth, latency, and compression/decompression costs.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TransmissionMetrics:
    """Metrics for transmission time analysis."""

    uncompressed_size_bits: int  # Original data size in bits
    compressed_size_bits: int  # Compressed data size in bits
    compression_time_ns: int  # Time to compress in nanoseconds
    decompression_time_ns: int  # Time to decompress in nanoseconds
    bandwidth_bps: float  # Network bandwidth in bits per second
    latency_ns: int  # Network latency in nanoseconds

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio (original / compressed)."""
        if self.compressed_size_bits == 0:
            return float("inf")
        return self.uncompressed_size_bits / self.compressed_size_bits

    @property
    def uncompressed_transmission_time_ns(self) -> float:
        """Time to transmit uncompressed data (transmission only)."""
        return (self.uncompressed_size_bits / self.bandwidth_bps) * 1e9

    @property
    def compressed_transmission_time_ns(self) -> float:
        """Time to transmit compressed data (transmission only)."""
        return (self.compressed_size_bits / self.bandwidth_bps) * 1e9

    @property
    def total_uncompressed_time_ns(self) -> float:
        """Total time without compression (latency + transmission)."""
        return self.latency_ns + self.uncompressed_transmission_time_ns

    @property
    def total_compressed_time_ns(self) -> float:
        """Total time with compression (latency + compress + transmit + decompress)."""
        return (
            self.latency_ns
            + self.compression_time_ns
            + self.compressed_transmission_time_ns
            + self.decompression_time_ns
        )

    @property
    def time_saved_ns(self) -> float:
        """Time saved by using compression (negative means slower)."""
        return self.total_uncompressed_time_ns - self.total_compressed_time_ns

    @property
    def is_compression_beneficial(self) -> bool:
        """Whether compression reduces total transmission time."""
        return self.time_saved_ns > 0

    def format_report(self) -> str:
        """Generate a human-readable report."""
        lines = [
            "Transmission Analysis Report",
            "=" * 50,
            f"Uncompressed size: {self.uncompressed_size_bits:,} bits "
            f"({self.uncompressed_size_bits // 8:,} bytes)",
            f"Compressed size: {self.compressed_size_bits:,} bits "
            f"({self.compressed_size_bits // 8:,} bytes)",
            f"Compression ratio: {self.compression_ratio:.2f}x",
            "",
            "Timing Breakdown:",
            f"  Network latency: {self.latency_ns / 1e6:.3f} ms",
            f"  Compression time: {self.compression_time_ns / 1e6:.3f} ms",
            f"  Decompression time: {self.decompression_time_ns / 1e6:.3f} ms",
            "",
            f"Uncompressed transmission: {self.uncompressed_transmission_time_ns / 1e6:.3f} ms",
            f"Compressed transmission: {self.compressed_transmission_time_ns / 1e6:.3f} ms",
            "",
            f"Total time (uncompressed): {self.total_uncompressed_time_ns / 1e6:.3f} ms",
            f"Total time (compressed): {self.total_compressed_time_ns / 1e6:.3f} ms",
            "",
        ]

        if self.is_compression_beneficial:
            lines.append(
                f"✓ Compression saves {self.time_saved_ns / 1e6:.3f} ms "
                f"({self.time_saved_ns / self.total_uncompressed_time_ns * 100:.1f}% faster)"
            )
        else:
            lines.append(
                f"✗ Compression adds {-self.time_saved_ns / 1e6:.3f} ms overhead "
                f"({-self.time_saved_ns / self.total_uncompressed_time_ns * 100:.1f}% slower)"
            )

        return "\n".join(lines)


def calculate_minimum_bandwidth_for_benefit(
    uncompressed_size_bits: int,
    compressed_size_bits: int,
    compression_time_ns: int,
    decompression_time_ns: int,
    latency_ns: int = 0,
) -> Optional[float]:
    """Calculate the minimum bandwidth where compression becomes beneficial.

    Args:
        uncompressed_size_bits: Size of uncompressed data in bits
        compressed_size_bits: Size of compressed data in bits
        compression_time_ns: Time to compress in nanoseconds
        decompression_time_ns: Time to decompress in nanoseconds
        latency_ns: Network latency in nanoseconds (default: 0)

    Returns:
        Minimum bandwidth in bits per second, or None if compression never beneficial
    """
    # Total overhead from compression/decompression
    overhead_ns = compression_time_ns + decompression_time_ns

    # For compression to be beneficial:
    # latency + overhead + compressed/bandwidth < latency + uncompressed/bandwidth
    # overhead + compressed/bandwidth < uncompressed/bandwidth
    # overhead < (uncompressed - compressed) / bandwidth
    # bandwidth < (uncompressed - compressed) / overhead

    size_saved_bits = uncompressed_size_bits - compressed_size_bits

    if size_saved_bits <= 0:
        # Compression doesn't reduce size
        return None

    if overhead_ns <= 0:
        # No overhead, compression always beneficial if size reduced
        return 0.0

    # Minimum bandwidth (bits per second)
    min_bandwidth_bps = (size_saved_bits / overhead_ns) * 1e9

    return min_bandwidth_bps


def analyze_scenarios(
    uncompressed_size_bits: int,
    compressed_size_bits: int,
    compression_time_ns: int,
    decompression_time_ns: int,
) -> str:
    """Analyze various network scenarios to see when compression helps.

    Args:
        uncompressed_size_bits: Size of uncompressed data in bits
        compressed_size_bits: Size of compressed data in bits
        compression_time_ns: Time to compress in nanoseconds
        decompression_time_ns: Time to decompress in nanoseconds

    Returns:
        Formatted report string
    """
    scenarios = [
        ("10 Gbps LAN (low latency)", 10e9, 100_000),  # 0.1ms latency
        ("1 Gbps LAN", 1e9, 500_000),  # 0.5ms latency
        ("100 Mbps", 100e6, 1_000_000),  # 1ms latency
        ("10 Mbps", 10e6, 5_000_000),  # 5ms latency
        ("1 Mbps", 1e6, 20_000_000),  # 20ms latency
        ("56 Kbps modem", 56e3, 100_000_000),  # 100ms latency
    ]

    lines = [
        "Network Scenario Analysis",
        "=" * 70,
        "",
    ]

    for name, bandwidth_bps, latency_ns in scenarios:
        metrics = TransmissionMetrics(
            uncompressed_size_bits=uncompressed_size_bits,
            compressed_size_bits=compressed_size_bits,
            compression_time_ns=compression_time_ns,
            decompression_time_ns=decompression_time_ns,
            bandwidth_bps=bandwidth_bps,
            latency_ns=latency_ns,
        )

        status = "✓ BENEFICIAL" if metrics.is_compression_beneficial else "✗ NOT BENEFICIAL"
        time_diff_ms = metrics.time_saved_ns / 1e6

        lines.append(f"{name:30} {status}")
        lines.append(
            f"  Uncompressed: {metrics.total_uncompressed_time_ns / 1e6:8.3f} ms | "
            f"Compressed: {metrics.total_compressed_time_ns / 1e6:8.3f} ms | "
            f"Diff: {time_diff_ms:+8.3f} ms"
        )
        lines.append("")

    # Calculate threshold
    min_bw = calculate_minimum_bandwidth_for_benefit(
        uncompressed_size_bits,
        compressed_size_bits,
        compression_time_ns,
        decompression_time_ns,
        0,  # No latency for threshold calculation
    )

    if min_bw is not None:
        lines.append(f"Minimum bandwidth for benefit: {min_bw / 1e6:.2f} Mbps (ignoring latency)")
    else:
        lines.append("Compression never beneficial (no size reduction)")

    return "\n".join(lines)
