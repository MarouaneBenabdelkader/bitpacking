"""Tests for non-crossing bit packing implementation."""

import random

import pytest

from bitpacking.noncross import BitPackingNonCross


class TestBitPackingNonCross:
    """Test suite for BitPackingNonCross."""

    def test_round_trip_small(self):
        """Test basic round-trip compression and decompression."""
        bp = BitPackingNonCross()
        data = [1, 5, 3, 7, 2, 8, 4, 6]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_round_trip_empty(self):
        """Test empty array."""
        bp = BitPackingNonCross()
        data = []
        packed = bp.compress(data)
        assert packed == {"k": 0, "n": 0, "words": []}
        restored = bp.decompress(packed)
        assert restored == []

    def test_round_trip_all_zeros(self):
        """Test all-zero array (k=0 case)."""
        bp = BitPackingNonCross()
        data = [0, 0, 0, 0, 0]
        packed = bp.compress(data)
        assert packed["k"] == 0
        assert packed["n"] == 5
        restored = bp.decompress(packed)
        assert restored == data

    def test_round_trip_single_element(self):
        """Test single element array."""
        bp = BitPackingNonCross()
        data = [42]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_round_trip_random(self):
        """Test round-trip with random data."""
        bp = BitPackingNonCross()
        random.seed(42)
        data = [random.randint(0, 1000) for _ in range(100)]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

    def test_edge_k1(self):
        """Test edge case: k=1 (binary values)."""
        bp = BitPackingNonCross()
        data = [0, 1, 1, 0, 1, 0, 1, 1] * 10
        packed = bp.compress(data)
        assert packed["k"] == 1
        restored = bp.decompress(packed)
        assert restored == data

    def test_edge_k16(self):
        """Test edge case: k=16."""
        bp = BitPackingNonCross()
        # Max value that requires 16 bits
        data = [65535, 32768, 16384, 8192]
        packed = bp.compress(data)
        assert packed["k"] == 16
        restored = bp.decompress(packed)
        assert restored == data

    def test_edge_k31(self):
        """Test edge case: k=31."""
        bp = BitPackingNonCross()
        # Max value that requires 31 bits
        data = [2147483647, 1073741824, 536870912]
        packed = bp.compress(data)
        assert packed["k"] == 31
        restored = bp.decompress(packed)
        assert restored == data

    def test_get_random_access(self):
        """Test random access with get()."""
        bp = BitPackingNonCross()
        data = [10, 20, 30, 40, 50, 60, 70, 80]
        bp.compress(data)

        for i, expected in enumerate(data):
            assert bp.get(i) == expected

    def test_get_random_indices(self):
        """Test get() with random indices."""
        bp = BitPackingNonCross()
        random.seed(123)
        data = [random.randint(0, 1000) for _ in range(1000)]
        bp.compress(data)

        # Test 100 random indices
        for _ in range(100):
            i = random.randint(0, len(data) - 1)
            assert bp.get(i) == data[i]

    def test_get_out_of_bounds(self):
        """Test get() with out of bounds index."""
        bp = BitPackingNonCross()
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
        bp = BitPackingNonCross()
        with pytest.raises(RuntimeError):
            bp.get(0)

    def test_negative_values_raise_error(self):
        """Test that negative values raise ValueError."""
        bp = BitPackingNonCross()
        data = [1, 2, -3, 4]
        with pytest.raises(ValueError, match="non-negative"):
            bp.compress(data)

    def test_property_decompress_compress_identity(self):
        """Property test: decompress(compress(A)) == A."""
        bp = BitPackingNonCross()
        random.seed(456)
        for _ in range(20):
            n = random.randint(1, 200)
            max_val = random.choice([1, 255, 65535, 1000000])
            data = [random.randint(0, max_val) for _ in range(n)]
            packed = bp.compress(data)
            restored = bp.decompress(packed)
            assert restored == data, f"Failed for n={n}, max_val={max_val}"

    def test_bit_width_correctness(self):
        """Test that k is correct for various max values."""
        bp = BitPackingNonCross()

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

    def test_capacity_calculation(self):
        """Test that capacity per word is correct."""
        bp = BitPackingNonCross()

        # k=1: capacity=32
        data = [1] * 100
        packed = bp.compress(data)
        assert packed["k"] == 1
        # Should need 4 words for 100 values (100/32 = 3.125 -> 4)
        assert len(packed["words"]) == 4

        # k=8: capacity=4
        data = [255] * 100
        packed = bp.compress(data)
        assert packed["k"] == 8
        # Should need 25 words for 100 values (100/4 = 25)
        assert len(packed["words"]) == 25

        # k=16: capacity=2
        data = [65535] * 100
        packed = bp.compress(data)
        assert packed["k"] == 16
        # Should need 50 words for 100 values (100/2 = 50)
        assert len(packed["words"]) == 50

    def test_words_are_uint32(self):
        """Test that all words are valid uint32 values."""
        bp = BitPackingNonCross()
        data = [random.randint(0, 65535) for _ in range(100)]
        packed = bp.compress(data)

        for word in packed["words"]:
            assert 0 <= word < 2**32, f"Word {word} not in uint32 range"

    def test_large_array(self):
        """Test with large array to ensure performance."""
        bp = BitPackingNonCross()
        random.seed(789)
        data = [random.randint(0, 255) for _ in range(10000)]
        packed = bp.compress(data)
        restored = bp.decompress(packed)
        assert restored == data

        # Test random access on large array
        for _ in range(100):
            i = random.randint(0, len(data) - 1)
            assert bp.get(i) == data[i]

    def test_sequential_compress_calls(self):
        """Test that compress() can be called multiple times."""
        bp = BitPackingNonCross()

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
