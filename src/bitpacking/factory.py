"""Factory for creating bit packing implementations by name."""

from bitpacking.base import BitPacking
from bitpacking.cross import BitPackingCrossed
from bitpacking.noncross import BitPackingNonCross
from bitpacking.overflow import BitPackingOverflow


def get_bitpacking(name: str = "noncross", **kwargs) -> BitPacking:
    """
    Get a bit packing implementation by name.

    Args:
        name: Name of implementation. Options:
            - "noncross": Non-crossing bit packing (default)
            - "cross": Crossing bit packing (values can span word boundaries)
            - "overflow": Overflow bit packing (separate storage for large values)
            - "overflow-cross": Overflow with crossing
            - "overflow-noncross": Overflow without crossing
        **kwargs: Additional arguments passed to implementation constructor.
            For overflow: crossing (bool), overflow_threshold (float)

    Returns:
        BitPacking implementation instance.

    Raises:
        ValueError: If name is not recognized.

    Example:
        >>> bp = get_bitpacking("noncross")
        >>> packed = bp.compress([1, 2, 3, 4])
        >>> bp_overflow = get_bitpacking("overflow", crossing=True, overflow_threshold=0.9)
    """
    if name == "overflow":
        return BitPackingOverflow(
            crossing=kwargs.get("crossing", True),
            overflow_threshold=kwargs.get("overflow_threshold", 0.95),
        )
    elif name == "overflow-cross":
        return BitPackingOverflow(
            crossing=True, overflow_threshold=kwargs.get("overflow_threshold", 0.95)
        )
    elif name == "overflow-noncross":
        return BitPackingOverflow(
            crossing=False, overflow_threshold=kwargs.get("overflow_threshold", 0.95)
        )

    implementations = {
        "noncross": BitPackingNonCross,
        "cross": BitPackingCrossed,
    }

    if name not in implementations:
        available = ", ".join(implementations.keys())
        raise ValueError(f"Unknown implementation '{name}'. Available: {available}")

    return implementations[name]()
