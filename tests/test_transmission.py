"""Tests for transmission time analysis."""

import pytest

from bitpacking.transmission import (
    TransmissionMetrics,
    analyze_scenarios,
    calculate_minimum_bandwidth_for_benefit,
)


class TestTransmissionMetrics:
    """Tests for TransmissionMetrics class."""

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        metrics = TransmissionMetrics(
            uncompressed_size_bits=32000,
            compressed_size_bits=8000,
            compression_time_ns=1000,
            decompression_time_ns=500,
            bandwidth_bps=1e9,
            latency_ns=1000,
        )
        assert metrics.compression_ratio == 4.0

    def test_transmission_time_calculation(self):
        """Test transmission time calculations."""
        metrics = TransmissionMetrics(
            uncompressed_size_bits=32000,  # 32kb
            compressed_size_bits=8000,  # 8kb
            compression_time_ns=1_000_000,  # 1ms
            decompression_time_ns=500_000,  # 0.5ms
            bandwidth_bps=1e6,  # 1 Mbps
            latency_ns=10_000_000,  # 10ms
        )

        # Uncompressed transmission: 32000 bits / 1e6 bps = 0.032s = 32ms
        assert metrics.uncompressed_transmission_time_ns == pytest.approx(32_000_000)

        # Compressed transmission: 8000 bits / 1e6 bps = 0.008s = 8ms
        assert metrics.compressed_transmission_time_ns == pytest.approx(8_000_000)

        # Total uncompressed: 10ms latency + 32ms transmission = 42ms
        assert metrics.total_uncompressed_time_ns == pytest.approx(42_000_000)

        # Total compressed: 10ms latency + 1ms compress + 8ms transmission + 0.5ms decompress
        # = 19.5ms
        assert metrics.total_compressed_time_ns == pytest.approx(19_500_000)

    def test_compression_beneficial_slow_network(self):
        """Compression should be beneficial on slow networks."""
        metrics = TransmissionMetrics(
            uncompressed_size_bits=32000,
            compressed_size_bits=8000,
            compression_time_ns=1_000_000,  # 1ms
            decompression_time_ns=500_000,  # 0.5ms
            bandwidth_bps=1e6,  # 1 Mbps (slow)
            latency_ns=10_000_000,
        )
        assert metrics.is_compression_beneficial is True
        assert metrics.time_saved_ns > 0

    def test_compression_not_beneficial_fast_network(self):
        """Compression may not be beneficial on very fast networks."""
        metrics = TransmissionMetrics(
            uncompressed_size_bits=32000,
            compressed_size_bits=8000,
            compression_time_ns=10_000_000,  # 10ms (slow compression)
            decompression_time_ns=5_000_000,  # 5ms (slow decompression)
            bandwidth_bps=10e9,  # 10 Gbps (fast)
            latency_ns=100_000,  # 0.1ms
        )
        # On fast network, transmission is negligible, compression overhead dominates
        assert metrics.is_compression_beneficial is False
        assert metrics.time_saved_ns < 0

    def test_format_report(self):
        """Test report generation."""
        metrics = TransmissionMetrics(
            uncompressed_size_bits=32000,
            compressed_size_bits=8000,
            compression_time_ns=1_000_000,
            decompression_time_ns=500_000,
            bandwidth_bps=1e6,
            latency_ns=10_000_000,
        )
        report = metrics.format_report()
        assert "Transmission Analysis Report" in report
        assert "Compression ratio: 4.00x" in report
        assert "saves" in report.lower() or "adds" in report.lower()


class TestMinimumBandwidth:
    """Tests for minimum bandwidth calculation."""

    def test_calculate_minimum_bandwidth(self):
        """Test minimum bandwidth calculation."""
        min_bw = calculate_minimum_bandwidth_for_benefit(
            uncompressed_size_bits=32000,
            compressed_size_bits=8000,
            compression_time_ns=1_000_000,  # 1ms
            decompression_time_ns=500_000,  # 0.5ms
            latency_ns=0,
        )

        # Size saved: 32000 - 8000 = 24000 bits
        # Overhead: 1ms + 0.5ms = 1.5ms = 1.5e6 ns
        # Min bandwidth: 24000 bits / 1.5e-3 s = 16e6 bps = 16 Mbps
        assert min_bw == pytest.approx(16e6)

    def test_minimum_bandwidth_no_size_reduction(self):
        """Test when compression doesn't reduce size."""
        min_bw = calculate_minimum_bandwidth_for_benefit(
            uncompressed_size_bits=1000,
            compressed_size_bits=1000,  # No reduction
            compression_time_ns=1_000_000,
            decompression_time_ns=500_000,
            latency_ns=0,
        )
        assert min_bw is None

    def test_minimum_bandwidth_size_increase(self):
        """Test when compression increases size."""
        min_bw = calculate_minimum_bandwidth_for_benefit(
            uncompressed_size_bits=1000,
            compressed_size_bits=1200,  # Increase!
            compression_time_ns=1_000_000,
            decompression_time_ns=500_000,
            latency_ns=0,
        )
        assert min_bw is None

    def test_minimum_bandwidth_zero_overhead(self):
        """Test with zero compression overhead."""
        min_bw = calculate_minimum_bandwidth_for_benefit(
            uncompressed_size_bits=32000,
            compressed_size_bits=8000,
            compression_time_ns=0,
            decompression_time_ns=0,
            latency_ns=0,
        )
        assert min_bw == 0.0


class TestAnalyzeScenarios:
    """Tests for scenario analysis."""

    def test_analyze_scenarios_output(self):
        """Test that analyze_scenarios produces expected output."""
        report = analyze_scenarios(
            uncompressed_size_bits=32000,
            compressed_size_bits=8000,
            compression_time_ns=1_000_000,
            decompression_time_ns=500_000,
        )

        assert "Network Scenario Analysis" in report
        assert "10 Gbps LAN" in report
        assert "56 Kbps modem" in report
        assert "BENEFICIAL" in report or "NOT BENEFICIAL" in report
        assert "Minimum bandwidth for benefit" in report

    def test_analyze_scenarios_shows_benefit_on_slow_networks(self):
        """Verify slow networks show compression as beneficial."""
        report = analyze_scenarios(
            uncompressed_size_bits=1_000_000,  # 1 Mb
            compressed_size_bits=250_000,  # 250 Kb (4x compression)
            compression_time_ns=1_000_000,  # 1ms
            decompression_time_ns=500_000,  # 0.5ms
        )

        # Should be beneficial on slow networks
        lines = report.split("\n")
        modem_lines = [line for line in lines if "56 Kbps" in line or "1 Mbps" in line]
        assert any("✓ BENEFICIAL" in line for line in modem_lines)
