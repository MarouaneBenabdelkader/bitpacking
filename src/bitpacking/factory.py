"""Factory for creating bit packing implementations by name."""

from bitpacking.base import BitPacking
from bitpacking.cross import BitPackingCrossed
from bitpacking.noncross import BitPackingNonCross


def get_bitpacking(name: str = "noncross") -> BitPacking:
    """
    Get a bit packing implementation by name.

    Args:
        name: Name of implementation. Options:
            - "noncross": Non-crossing bit packing (default)
            - "cross": Crossing bit packing (values can span word boundaries)

    Returns:
        BitPacking implementation instance.

    Raises:
        ValueError: If name is not recognized.

    Example:
        >>> bp = get_bitpacking("noncross")
        >>> packed = bp.compress([1, 2, 3, 4])
    """
    implementations = {
        "noncross": BitPackingNonCross,
        "cross": BitPackingCrossed,
    }

    if name not in implementations:
        available = ", ".join(implementations.keys())
        raise ValueError(f"Unknown implementation '{name}'. Available: {available}")

    return implementations[name]()
