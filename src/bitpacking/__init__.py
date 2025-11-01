"""bitpacking: Integer-array compression with direct random access."""

from bitpacking.base import BitPacking
from bitpacking.cross import BitPackingCrossed
from bitpacking.factory import get_bitpacking
from bitpacking.noncross import BitPackingNonCross
from bitpacking.overflow import BitPackingOverflow
from bitpacking.transmission import (
    TransmissionMetrics,
    analyze_scenarios,
    calculate_minimum_bandwidth_for_benefit,
)

__version__ = "0.1.0"
__all__ = [
    "BitPacking",
    "BitPackingNonCross",
    "BitPackingCrossed",
    "BitPackingOverflow",
    "get_bitpacking",
    "TransmissionMetrics",
    "analyze_scenarios",
    "calculate_minimum_bandwidth_for_benefit",
]
