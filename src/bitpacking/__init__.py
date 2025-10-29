"""bitpacking: Integer-array compression with direct random access."""

from bitpacking.base import BitPacking
from bitpacking.cross import BitPackingCrossed
from bitpacking.factory import get_bitpacking
from bitpacking.noncross import BitPackingNonCross

__version__ = "0.1.0"
__all__ = ["BitPacking", "BitPackingNonCross", "BitPackingCrossed", "get_bitpacking"]
