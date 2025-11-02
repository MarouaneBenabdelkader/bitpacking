"""Tests for bit packing factory."""

import pytest

from bitpacking.cross import BitPackingCrossed
from bitpacking.factory import get_bitpacking
from bitpacking.noncross import BitPackingNonCross
from bitpacking.overflow import BitPackingOverflow


class TestFactory:
    """Test suite for get_bitpacking factory function."""

    def test_get_noncross(self):
        """Test getting non-cross implementation."""
        bp = get_bitpacking("noncross")
        assert isinstance(bp, BitPackingNonCross)

    def test_get_cross(self):
        """Test getting cross implementation."""
        bp = get_bitpacking("cross")
        assert isinstance(bp, BitPackingCrossed)

    def test_get_overflow(self):
        """Test getting overflow implementation."""
        bp = get_bitpacking("overflow")
        assert isinstance(bp, BitPackingOverflow)

    def test_get_overflow_cross(self):
        """Test getting overflow with crossing."""
        bp = get_bitpacking("overflow-cross")
        assert isinstance(bp, BitPackingOverflow)
        # Check it's configured for crossing
        data = [1, 2, 3]
        packed = bp.compress(data)
        assert packed["crossing"] is True

    def test_get_overflow_noncross(self):
        """Test getting overflow without crossing."""
        bp = get_bitpacking("overflow-noncross")
        assert isinstance(bp, BitPackingOverflow)
        # Check it's configured for non-crossing
        data = [1, 2, 3]
        packed = bp.compress(data)
        assert packed["crossing"] is False

    def test_default_implementation(self):
        """Test default implementation is noncross."""
        bp = get_bitpacking()
        assert isinstance(bp, BitPackingNonCross)

    def test_invalid_implementation_name(self):
        """Test invalid implementation name raises error."""
        with pytest.raises(ValueError):
            get_bitpacking("invalid")

    def test_overflow_default_threshold_is_075(self):
        """Test that factory creates overflow with default threshold 0.75."""
        bp = get_bitpacking("overflow")

        # Use the documentation example that works with 0.75 but not 0.95
        data = [1, 2, 3, 1024, 4, 5, 2048]
        packed = bp.compress(data)

        # With threshold 0.75, overflow should be used
        assert len(packed["overflow"]) == 2
        assert packed["overflow"] == [1024, 2048]
        assert packed["k"] == 4  # Should be 4, not 12

        # Verify correctness
        restored = bp.decompress(packed)
        assert restored == data

    def test_overflow_cross_default_threshold_is_075(self):
        """Test that overflow-cross uses default threshold 0.75."""
        bp = get_bitpacking("overflow-cross")
        data = [1, 2, 3, 1024, 4, 5, 2048]
        packed = bp.compress(data)

        # Should use overflow with threshold 0.75
        assert len(packed["overflow"]) == 2
        assert packed["crossing"] is True

    def test_overflow_noncross_default_threshold_is_075(self):
        """Test that overflow-noncross uses default threshold 0.75."""
        bp = get_bitpacking("overflow-noncross")
        data = [1, 2, 3, 1024, 4, 5, 2048]
        packed = bp.compress(data)

        # Should use overflow with threshold 0.75
        assert len(packed["overflow"]) == 2
        assert packed["crossing"] is False

    def test_overflow_custom_threshold_via_factory(self):
        """Test passing custom threshold through factory."""
        # High threshold (0.95) - should not use overflow for doc example
        bp_high = get_bitpacking("overflow", overflow_threshold=0.95)
        data = [1, 2, 3, 1024, 4, 5, 2048]
        packed_high = bp_high.compress(data)
        assert len(packed_high["overflow"]) == 0  # No overflow

        # Low threshold (0.6) - should use overflow
        bp_low = get_bitpacking("overflow", overflow_threshold=0.6)
        packed_low = bp_low.compress(data)
        assert len(packed_low["overflow"]) >= 2  # Uses overflow

    def test_overflow_custom_crossing_via_factory(self):
        """Test passing custom crossing parameter through factory."""
        bp = get_bitpacking("overflow", crossing=False)
        data = [1, 2, 3, 4, 5]
        packed = bp.compress(data)
        assert packed["crossing"] is False

    def test_factory_kwargs_passed_correctly(self):
        """Test that all kwargs are passed to implementation."""
        bp = get_bitpacking(
            "overflow",
            crossing=False,
            overflow_threshold=0.8
        )
        data = [1, 2, 3, 1024, 4, 5, 2048]
        packed = bp.compress(data)

        # Check both parameters were applied
        assert packed["crossing"] is False
        # With threshold 0.8, should still use overflow for this data
        assert len(packed["overflow"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
