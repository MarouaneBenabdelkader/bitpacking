"""Tests for overflow bit packing implementation."""

import random

import pytest

from bitpacking.overflow import BitPackingOverflow


class TestBitPackingOverflow:
    """Test suite for BitPackingOverflow."""

    def test_example_from_spec(self):
        """Test the exact example from specification."""
        bp = BitPackingOverflow(crossing=True, overflow_threshold=0.6)
        data = [1, 2, 3, 1024, 4, 5, 2048]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data
        # The exact overflow behavior depends on threshold, just verify correctness

    def test_round_trip_with_overflow(self):
        """Test round-trip with values that trigger overflow."""
        bp = BitPackingOverflow(crossing=True)
        # Most values small, few large
        data = [1, 2, 3, 4, 5] + [10000] * 2
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_round_trip_no_overflow_needed(self):
        """Test when all values fit without overflow."""
        bp = BitPackingOverflow(crossing=True)
        data = [1, 5, 3, 7, 2, 8, 4, 6]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data
        assert len(packed["overflow"]) == 0

    def test_empty_array(self):
        """Test empty array."""
        bp = BitPackingOverflow(crossing=True)
        data = []
        packed = bp.compress(data)
        assert packed["n"] == 0
        restored = bp.decompress(packed)
        assert restored == []

    def test_all_zeros(self):
        """Test all-zero array."""
        bp = BitPackingOverflow(crossing=True)
        data = [0, 0, 0, 0, 0]
        packed = bp.compress(data)
        assert packed["k"] == 0
        restored = bp.decompress(packed)
        assert restored == data

    def test_single_element(self):
        """Test single element."""
        bp = BitPackingOverflow(crossing=True)
        data = [42]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_get_with_overflow(self):
        """Test get() with overflow values."""
        bp = BitPackingOverflow(crossing=True)
        data = [1, 2, 1000, 3, 4, 2000]
        bp.compress(data)

        for i, expected in enumerate(data):
            assert bp.get(i) == expected

    def test_get_random_indices(self):
        """Test get() with random indices."""
        bp = BitPackingOverflow(crossing=True)
        random.seed(123)
        # Mix of small and large values
        data = [random.randint(0, 100) for _ in range(90)] + [
            random.randint(10000, 100000) for _ in range(10)
        ]
        random.shuffle(data)
        bp.compress(data)

        for _ in range(20):
            i = random.randint(0, len(data) - 1)
            assert bp.get(i) == data[i]

    def test_noncrossing_mode(self):
        """Test overflow with non-crossing mode."""
        bp = BitPackingOverflow(crossing=False)
        data = [1, 2, 3, 1000, 4, 5, 2000]
        packed = bp.compress(data)
        assert packed["crossing"] is False
        restored = bp.decompress(packed)
        assert restored == data

    def test_overflow_threshold(self):
        """Test different overflow thresholds."""
        data = list(range(100)) + [10000, 20000]

        # Lower threshold = more overflow
        bp_low = BitPackingOverflow(crossing=True, overflow_threshold=0.8)
        pack_low = bp_low.compress(data)

        # Higher threshold = less overflow
        bp_high = BitPackingOverflow(crossing=True, overflow_threshold=0.98)
        pack_high = bp_high.compress(data)

        # Both should decompress correctly
        assert bp_low.decompress(pack_low) == data
        assert bp_high.decompress(pack_high) == data

    def test_negative_values_raise_error(self):
        """Test that negative values raise ValueError."""
        bp = BitPackingOverflow(crossing=True)
        data = [1, 2, -3, 4]
        with pytest.raises(ValueError, match="non-negative"):
            bp.compress(data)

    def test_get_out_of_bounds(self):
        """Test get() with out of bounds index."""
        bp = BitPackingOverflow(crossing=True)
        data = [1, 2, 3]
        bp.compress(data)

        with pytest.raises(IndexError):
            bp.get(-1)
        with pytest.raises(IndexError):
            bp.get(3)

    def test_get_before_compress(self):
        """Test get() before compress() raises error."""
        bp = BitPackingOverflow(crossing=True)
        with pytest.raises(RuntimeError):
            bp.get(0)

    def test_compression_benefit(self):
        """Test that overflow provides compression benefit."""
        # Array where overflow is beneficial
        data = [random.randint(0, 127) for _ in range(95)] + [100000] * 5

        bp_overflow = BitPackingOverflow(crossing=True, overflow_threshold=0.9)
        bp_no_overflow = BitPackingOverflow(crossing=True, overflow_threshold=1.0)

        pack_overflow = bp_overflow.compress(data)
        pack_no_overflow = bp_no_overflow.compress(data)

        # With overflow should use fewer bits in main area
        assert pack_overflow["k"] < pack_no_overflow["k"]

    def test_large_array_with_outliers(self):
        """Test large array with a few outliers."""
        bp = BitPackingOverflow(crossing=True)
        random.seed(999)
        # 1000 small values, 10 large values
        data = [random.randint(0, 255) for _ in range(1000)] + [
            random.randint(100000, 1000000) for _ in range(10)
        ]
        random.shuffle(data)

        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

        # Verify overflow was used
        assert len(packed["overflow"]) > 0

        # Test random access
        for _ in range(50):
            i = random.randint(0, len(data) - 1)
            assert bp.get(i) == data[i]

    def test_sequential_compress_calls(self):
        """Test that compress() can be called multiple times."""
        bp = BitPackingOverflow(crossing=True)

        data1 = [1, 2, 3, 1000]
        pack1 = bp.compress(data1)
        assert bp.get(0) == 1
        assert bp.get(3) == 1000

        data2 = [10, 20, 30, 40]
        pack2 = bp.compress(data2)
        assert bp.get(0) == 10
        assert bp.get(3) == 40

        # Packs should be different
        assert pack1["n"] == 4
        assert pack2["n"] == 4

    def test_property_decompress_compress_identity(self):
        """Property test: decompress(compress(A)) == A."""
        bp = BitPackingOverflow(crossing=True)
        random.seed(456)

        for _ in range(10):
            n = random.randint(10, 100)
            # Mix of small and large values
            small_count = int(n * 0.9)
            large_count = n - small_count
            data = [random.randint(0, 255) for _ in range(small_count)]
            data += [random.randint(10000, 100000) for _ in range(large_count)]
            random.shuffle(data)

            packed = bp.compress(data)
            restored = bp.decompress(packed)
            assert restored == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
