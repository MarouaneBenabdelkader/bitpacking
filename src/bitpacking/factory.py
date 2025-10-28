"""Factory for creating bit packing implementations by name."""

from bitpacking.base import BitPacking
from bitpacking.noncross import BitPackingNonCross


def get_bitpacking(name: str = "noncross") -> BitPacking:
    """
    Get a bit packing implementation by name.

    Args:
        name: Name of implementation. Options:
            - "noncross": Non-crossing bit packing (default)

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
    }

    if name not in implementations:
        available = ", ".join(implementations.keys())
        raise ValueError(f"Unknown implementation '{name}'. Available: {available}")

    return implementations[name]()
