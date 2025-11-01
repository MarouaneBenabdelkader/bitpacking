"""Non-crossing bit packing implementation.

This implementation uses fixed bit-width k for all values and ensures
no value crosses 32-bit word boundaries, enabling O(1) random access.
"""

from bitpacking.base import BitPacking


class BitPackingNonCross(BitPacking):
    """
    Non-crossing bit packing with fixed bit-width per block.

    Values are packed into 32-bit words without crossing boundaries.
    This enables direct O(1) element access at the cost of some wasted bits.
    """

    def __init__(self):
        """Initialize non-crossing bit packing."""
        self._pack = None

    def compress(self, int_list: list[int]) -> dict:
        """
        Compress a list of non-negative integers using non-crossing bit packing.

        Args:
            int_list: List of non-negative integers.

        Returns:
            Dictionary with:
            - "k": bit width (minimum bits to represent max value)
            - "n": number of values
            - "words": list of uint32 words in little-endian bit order

        Raises:
            ValueError: If any value is negative.

        Algorithm:
            1. Find k = bit_length of max value (or 0 for all-zero)
            2. Calculate capacity = 32 // k (values per word)
            3. Pack values: word[i // capacity] |= value << (slot * k)
               where slot = i % capacity, bit_offset = slot * k
            4. Mask ensures value fits: (1 << k) - 1
        """
        if not int_list:
            return {"k": 0, "n": 0, "words": []}

        # Validate all non-negative
        if any(x < 0 for x in int_list):
            raise ValueError("All values must be non-negative")

        n = len(int_list)
        max_val = max(int_list)

        # Special case: all zeros
        if max_val == 0:
            k = 0
            # For k=0, we need at least minimal representation
            # Store n zeros as empty words (no bits needed)
            return {"k": 0, "n": n, "words": []}

        # Calculate minimum bit width
        k = max_val.bit_length()

        # Calculate capacity per 32-bit word
        # Each value takes k bits and cannot cross word boundary
        capacity = 32 // k

        if capacity == 0:
            raise ValueError(f"Value {max_val} requires {k} bits, exceeds 32-bit word size")

        # Calculate number of words needed
        num_words = (n + capacity - 1) // capacity

        # Initialize words as uint32 (Python ints in [0, 2^32-1])
        words = [0] * num_words

        # Pack values into words
        mask = (1 << k) - 1
        for i, value in enumerate(int_list):
            # Determine which word and slot within that word
            word_idx = i // capacity
            slot = i % capacity
            bit_offset = slot * k

            # Pack value at bit_offset within the word
            # Little-endian bit order: lower bits first
            words[word_idx] |= (value & mask) << bit_offset

        self._pack = {"k": k, "n": n, "words": words}
        return self._pack

    def decompress(self, pack: dict) -> list[int]:
        """
        Decompress packed representation to original list.

        Args:
            pack: Dictionary with "k", "n", "words" keys.

        Returns:
            List of n decompressed integers.

        Algorithm:
            1. Extract k, n from pack
            2. For k=0, return [0] * n
            3. Otherwise, extract each value from words:
               word[i // capacity] >> (slot * k) & mask
        """
        k = pack["k"]
        n = pack["n"]
        words = pack["words"]

        if n == 0:
            return []

        # Special case: k=0 means all zeros
        if k == 0:
            return [0] * n

        capacity = 32 // k
        mask = (1 << k) - 1
        result = []

        for i in range(n):
            word_idx = i // capacity
            slot = i % capacity
            bit_offset = slot * k

            # Extract value from word
            value = (words[word_idx] >> bit_offset) & mask
            result.append(value)

        return result

    def get(self, i: int) -> int:
        """
        Retrieve element at index i in O(1) time.

        Args:
            i: Index of element to retrieve.

        Returns:
            Value at index i.

        Raises:
            IndexError: If index out of bounds.
            RuntimeError: If compress() has not been called.

        Algorithm (O(1)):
            1. word_idx = i // capacity
            2. slot = i % capacity
            3. bit_offset = slot * k
            4. value = words[word_idx] >> bit_offset & mask
        """
        if self._pack is None:
            raise RuntimeError("Must call compress() before get()")

        n = self._pack["n"]
        if i < 0 or i >= n:
            raise IndexError(f"Index {i} out of bounds for length {n}")

        k = self._pack["k"]
        words = self._pack["words"]

        # Special case: k=0 means all zeros
        if k == 0:
            return 0

        capacity = 32 // k
        word_idx = i // capacity
        slot = i % capacity
        bit_offset = slot * k
        mask = (1 << k) - 1

        # Extract and return value
        value = (words[word_idx] >> bit_offset) & mask
        return value

    def load(self, pack: dict) -> None:
        """
        Load a previously compressed representation to enable get() operations.

        Args:
            pack: Dictionary with compressed data from compress().
        """
        self._pack = pack
