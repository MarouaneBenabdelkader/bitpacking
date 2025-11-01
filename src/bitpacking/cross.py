"""Crossing bit packing implementation.

This implementation allows values to cross 32-bit word boundaries,
achieving better compression at the cost of slightly more complex access logic.
Values are packed sequentially with a global bit pointer across all words.
"""

from bitpacking.base import BitPacking


class BitPackingCrossed(BitPacking):
    """
    Crossing bit packing where values can span word boundaries.

    Unlike non-crossing, this implementation packs values sequentially
    across 32-bit words without alignment constraints. A value may be
    split between two consecutive words, requiring bit manipulation
    across word boundaries during read/write.

    This achieves optimal space usage: total_bits = n * k exactly,
    with no wasted bits due to alignment padding.
    """

    def __init__(self):
        """Initialize crossing bit packing."""
        self._pack = None

    def compress(self, int_list: list[int]) -> dict:
        """
        Compress a list of non-negative integers using crossing bit packing.

        Args:
            int_list: List of non-negative integers.

        Returns:
            Dictionary with:
            - "k": bit width (minimum bits to represent max value)
            - "n": number of values
            - "words": list of uint32 words

        Raises:
            ValueError: If any value is negative.

        Algorithm:
            1. Compute k = bit_length(max value)
            2. Initialize global bit position = 0
            3. For each value:
                - current_word = bit_pos // 32
                - bit_offset = bit_pos % 32
                - bits_remaining = 32 - bit_offset
                - If k <= bits_remaining:
                    Write all k bits to current word
                - Else:
                    Write lower bits_remaining bits to current word
                    Write upper (k - bits_remaining) bits to next word
                - Increment bit_pos by k
            4. Return packed words
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
            return {"k": 0, "n": n, "words": []}

        # Calculate minimum bit width
        k = max_val.bit_length()

        if k > 32:
            raise ValueError(f"Value {max_val} requires {k} bits, exceeds 32-bit word size")

        # Calculate total bits needed and number of words
        total_bits = n * k
        num_words = (total_bits + 31) // 32  # Ceiling division

        # Initialize words
        words = [0] * num_words

        # Pack values with crossing
        bit_pos = 0
        mask = (1 << k) - 1

        for value in int_list:
            value &= mask  # Ensure value fits in k bits

            # Determine current word and bit offset within that word
            word_idx = bit_pos // 32
            bit_offset = bit_pos % 32
            bits_remaining = 32 - bit_offset

            if k <= bits_remaining:
                # Value fits entirely in current word
                words[word_idx] |= value << bit_offset
            else:
                # Value spans two words
                # Lower part: bits_remaining bits go to current word
                lower_bits = value & ((1 << bits_remaining) - 1)
                words[word_idx] |= lower_bits << bit_offset

                # Upper part: (k - bits_remaining) bits go to next word
                upper_bits = value >> bits_remaining
                words[word_idx + 1] |= upper_bits

            bit_pos += k

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
            3. For each index i from 0 to n-1:
                - bit_offset = i * k
                - word_idx = bit_offset // 32
                - bit_in_word = bit_offset % 32
                - bits_remaining = 32 - bit_in_word
                - If k <= bits_remaining:
                    Extract k bits from current word
                - Else:
                    Extract bits_remaining bits from current word (lower part)
                    Extract (k - bits_remaining) bits from next word (upper part)
                    Combine them
        """
        k = pack["k"]
        n = pack["n"]
        words = pack["words"]

        if n == 0:
            return []

        # Special case: k=0 means all zeros
        if k == 0:
            return [0] * n

        mask = (1 << k) - 1
        result = []

        for i in range(n):
            bit_offset = i * k
            word_idx = bit_offset // 32
            bit_in_word = bit_offset % 32
            bits_remaining = 32 - bit_in_word

            if k <= bits_remaining:
                # Value entirely in current word
                value = (words[word_idx] >> bit_in_word) & mask
            else:
                # Value spans two words
                # Lower part from current word
                lower_mask = (1 << bits_remaining) - 1
                lower_bits = (words[word_idx] >> bit_in_word) & lower_mask

                # Upper part from next word
                upper_bits_count = k - bits_remaining
                upper_mask = (1 << upper_bits_count) - 1
                upper_bits = words[word_idx + 1] & upper_mask

                # Combine: upper bits shifted left, then OR with lower bits
                value = (upper_bits << bits_remaining) | lower_bits

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
            1. bit_offset = i * k
            2. word_idx = bit_offset // 32
            3. bit_in_word = bit_offset % 32
            4. bits_remaining = 32 - bit_in_word
            5. If k <= bits_remaining:
                Extract from single word
               Else:
                Extract and combine from two words
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

        # Calculate bit position for this index
        bit_offset = i * k
        word_idx = bit_offset // 32
        bit_in_word = bit_offset % 32
        bits_remaining = 32 - bit_in_word
        mask = (1 << k) - 1

        if k <= bits_remaining:
            # Value entirely in current word
            value = (words[word_idx] >> bit_in_word) & mask
        else:
            # Value spans two words
            # Lower part from current word
            lower_mask = (1 << bits_remaining) - 1
            lower_bits = (words[word_idx] >> bit_in_word) & lower_mask

            # Upper part from next word
            upper_bits_count = k - bits_remaining
            upper_mask = (1 << upper_bits_count) - 1
            upper_bits = words[word_idx + 1] & upper_mask

            # Combine
            value = (upper_bits << bits_remaining) | lower_bits

        return value

    def load(self, pack: dict) -> None:
        """
        Load a previously compressed representation to enable get() operations.

        Args:
            pack: Dictionary with compressed data from compress().
        """
        self._pack = pack
