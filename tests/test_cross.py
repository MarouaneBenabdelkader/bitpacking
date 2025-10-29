"""Tests for crossing bit packing implementation."""

import random

import pytest

from bitpacking.cross import BitPackingCrossed
from bitpacking.noncross import BitPackingNonCross


class TestBitPackingCrossed:
    """Test suite for BitPackingCrossed."""

    def test_round_trip_small(self):
        """Test basic round-trip compression and decompression."""
        bp = BitPackingCrossed()
        data = [1, 5, 3, 7, 2, 8, 4, 6]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_round_trip_empty(self):
        """Test empty array."""
        bp = BitPackingCrossed()
        data = []
        packed = bp.compress(data)
        assert packed == {"k": 0, "n": 0, "words": []}
        restored = bp.decompress(packed)
        assert restored == []

    def test_round_trip_all_zeros(self):
        """Test all-zero array (k=0 case)."""
        bp = BitPackingCrossed()
        data = [0, 0, 0, 0, 0]
        packed = bp.compress(data)
        assert packed["k"] == 0
        assert packed["n"] == 5
        restored = bp.decompress(packed)
        assert restored == data

    def test_round_trip_single_element(self):
        """Test single element array."""
        bp = BitPackingCrossed()
        data = [42]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_round_trip_random(self):
        """Test round-trip with random data."""
        bp = BitPackingCrossed()
        random.seed(42)
        data = [random.randint(0, 1000) for _ in range(100)]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_property_decompress_compress_identity(self):
        """Property test: decompress(compress(A)) == A."""
        bp = BitPackingCrossed()
        random.seed(456)
        for _ in range(20):
            n = random.randint(1, 200)
            max_val = random.choice([1, 255, 65535, 1000000])
            data = [random.randint(0, max_val) for _ in range(n)]
            packed = bp.compress(data)
            restored = bp.decompress(packed)
            assert restored == data, f"Failed for n={n}, max_val={max_val}"

    def test_get_random_access(self):
        """Test random access with get()."""
        bp = BitPackingCrossed()
        data = [10, 20, 30, 40, 50, 60, 70, 80]
        bp.compress(data)

        for i, expected in enumerate(data):
            assert bp.get(i) == expected

    def test_get_random_indices(self):
        """Test get() with random indices (10 random accesses)."""
        bp = BitPackingCrossed()
        random.seed(123)
        data = [random.randint(0, 1000) for _ in range(100)]
        bp.compress(data)

        # Test 10 random indices
        for _ in range(10):
            i = random.randint(0, len(data) - 1)
            assert bp.get(i) == data[i]

    def test_get_out_of_bounds(self):
        """Test get() with out of bounds index."""
        bp = BitPackingCrossed()
        data = [1, 2, 3]
        bp.compress(data)

        with pytest.raises(IndexError):
            bp.get(-1)

        with pytest.raises(IndexError):
            bp.get(3)

        with pytest.raises(IndexError):
            bp.get(100)

    def test_get_before_compress(self):
        """Test get() before compress() raises error."""
        bp = BitPackingCrossed()
        with pytest.raises(RuntimeError):
            bp.get(0)

    def test_negative_values_raise_error(self):
        """Test that negative values raise ValueError."""
        bp = BitPackingCrossed()
        data = [1, 2, -3, 4]
        with pytest.raises(ValueError, match="non-negative"):
            bp.compress(data)

    def test_forces_crossing(self):
        """Test case that forces values to cross word boundaries."""
        bp = BitPackingCrossed()
        # Use k=5 bits per value: 32/5 = 6.4, so values will cross boundaries
        # Values in range [0, 31] require 5 bits
        data = [31, 15, 7, 23, 11, 29, 3, 19, 27, 13] * 10
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

        # Verify random access works across boundaries
        for _ in range(10):
            i = random.randint(0, len(data) - 1)
            assert bp.get(i) == data[i]

    def test_k_not_dividing_32(self):
        """Test with k values that don't evenly divide 32."""
        bp = BitPackingCrossed()
        test_cases = [
            # k=3: 32/3 = 10.67 (forces crossing)
            ([7, 3, 5, 1, 6, 2, 4, 0] * 5, 3),
            # k=7: 32/7 = 4.57 (forces crossing)
            ([127, 64, 32, 16, 8, 100, 50, 75] * 3, 7),
            # k=13: 32/13 = 2.46 (forces crossing)
            ([8191, 4096, 2048, 1024] * 4, 13),
        ]

        for data, expected_k in test_cases:
            packed = bp.compress(data)
            assert packed["k"] == expected_k, f"Expected k={expected_k}, got {packed['k']}"
            restored = bp.decompress(packed)
            assert restored == data

    def test_compression_efficiency_vs_noncross(self):
        """Compare word count: cross should use fewer or equal words than noncross."""
        random.seed(789)
        data = [random.randint(0, 127) for _ in range(100)]  # k=7

        bp_cross = BitPackingCrossed()
        bp_noncross = BitPackingNonCross()

        pack_cross = bp_cross.compress(data)
        pack_noncross = bp_noncross.compress(data)

        # Cross should be more efficient (fewer words)
        assert len(pack_cross["words"]) <= len(pack_noncross["words"])
        # For k=7, n=100: cross needs ceil(700/32)=22, noncross needs ceil(100/4)=25
        assert len(pack_cross["words"]) == 22
        assert len(pack_noncross["words"]) == 25

    def test_bit_width_correctness(self):
        """Test that k is correct for various max values."""
        bp = BitPackingCrossed()

        # k=0 for all zeros
        assert bp.compress([0, 0, 0])["k"] == 0

        # k=1 for max=1
        assert bp.compress([0, 1, 0, 1])["k"] == 1

        # k=8 for max=255
        assert bp.compress([0, 255, 100])["k"] == 8

        # k=16 for max=65535
        assert bp.compress([0, 65535, 100])["k"] == 16

        # k=17 for max=65536
        assert bp.compress([0, 65536])["k"] == 17

    def test_words_are_uint32(self):
        """Test that all words are valid uint32 values."""
        bp = BitPackingCrossed()
        random.seed(999)
        data = [random.randint(0, 65535) for _ in range(100)]
        packed = bp.compress(data)

        for word in packed["words"]:
            assert 0 <= word < 2**32, f"Word {word} not in uint32 range"

    def test_sequential_compress_calls(self):
        """Test that compress() can be called multiple times."""
        bp = BitPackingCrossed()

        data1 = [1, 2, 3]
        pack1 = bp.compress(data1)
        assert bp.get(0) == 1

        data2 = [10, 20, 30, 40]
        pack2 = bp.compress(data2)
        assert bp.get(0) == 10
        assert bp.get(3) == 40

        # Ensure packs are different
        assert pack1["n"] == 3
        assert pack2["n"] == 4

    def test_large_array(self):
        """Test with large array."""
        bp = BitPackingCrossed()
        random.seed(111)
        data = [random.randint(0, 255) for _ in range(10000)]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

        # Test some random accesses
        for _ in range(20):
            i = random.randint(0, len(data) - 1)
            assert bp.get(i) == data[i]

    def test_edge_k1(self):
        """Test edge case: k=1 (binary values)."""
        bp = BitPackingCrossed()
        data = [0, 1, 1, 0, 1, 0, 1, 1] * 10
        packed = bp.compress(data)
        assert packed["k"] == 1
        restored = bp.decompress(packed)
        assert restored == data

    def test_edge_k16(self):
        """Test edge case: k=16."""
        bp = BitPackingCrossed()
        data = [65535, 32768, 16384, 8192]
        packed = bp.compress(data)
        assert packed["k"] == 16
        restored = bp.decompress(packed)
        assert restored == data

    def test_edge_k31(self):
        """Test edge case: k=31."""
        bp = BitPackingCrossed()
        data = [2147483647, 1073741824, 536870912]
        packed = bp.compress(data)
        assert packed["k"] == 31
        restored = bp.decompress(packed)
        assert restored == data

    def test_crossing_boundary_exact(self):
        """Test value that crosses exactly at word boundary."""
        bp = BitPackingCrossed()
        # Use k=17: first value at bits 0-16, second at 17-33 (crosses at 32)
        data = [131071, 131071]  # Max value for 17 bits
        packed = bp.compress(data)
        assert packed["k"] == 17
        restored = bp.decompress(packed)
        assert restored == data

        # Verify both values via get()
        assert bp.get(0) == 131071
        assert bp.get(1) == 131071


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
