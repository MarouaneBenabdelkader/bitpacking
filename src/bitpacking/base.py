"""Abstract base class for bit packing implementations."""

from abc import ABC, abstractmethod


class BitPacking(ABC):
    """Abstract interface for integer array compression with random access."""

    @abstractmethod
    def compress(self, int_list: list[int]) -> dict:
        """
        Compress a list of non-negative integers.

        Args:
            int_list: List of non-negative integers to compress.

        Returns:
            Dictionary containing compressed representation with keys:
            - "k": bit width per value
            - "n": number of values
            - "words": list of uint32 words storing packed bits

        Raises:
            ValueError: If any value is negative.
        """
        pass

    @abstractmethod
    def decompress(self, pack: dict) -> list[int]:
        """
        Decompress a packed representation back to original list.

        Args:
            pack: Dictionary with "k", "n", and "words" keys.

        Returns:
            List of decompressed integers.
        """
        pass

    @abstractmethod
    def get(self, i: int) -> int:
        """
        Retrieve element at index i in O(1) time.

        Args:
            i: Index of element to retrieve.

        Returns:
            Value at index i.

        Raises:
            IndexError: If index is out of bounds.
        """
        pass
