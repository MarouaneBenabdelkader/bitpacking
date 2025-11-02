"""Overflow bit packing implementation.

This implementation handles arrays where a few values require significantly
more bits than the majority. Instead of encoding all values with the maximum
bit width, we use an overflow area to store large values separately.

Example:
    [1, 2, 3, 1024, 4, 5, 2048]
    Instead of using 11 bits for all (max=2048), we use:
    - 4 bits for main area (3 bits for value + 1 bit overflow flag)
    - Overflow area: [1024, 2048]
    Result: 0-1, 0-2, 0-3, 1-0, 0-4, 0-5, 1-1, [1024, 2048]
"""

from bitpacking.base import BitPacking


class BitPackingOverflow(BitPacking):
    """
    Overflow bit packing with separate storage for large values.

    Uses a threshold to determine which values go to overflow area.
    Values above threshold are stored separately and referenced by index.
    Maintains O(1) random access through precomputed overflow positions.
    """

    def __init__(self, crossing: bool = True, overflow_threshold: float = 0.95):
        """
        Initialize overflow bit packing.

        Args:
            crossing: If True, use crossing implementation for main area.
                     If False, use non-crossing implementation.
            overflow_threshold: Percentile to use as overflow threshold (0-1).
                              Values above this percentile go to overflow.
        """
        self._pack: dict | None = None
        self._crossing = crossing
        self._overflow_threshold = overflow_threshold

    def _determine_overflow_strategy(self, int_list: list[int]) -> tuple[int, int, list[int]]:
        """
        Determine optimal bit widths and overflow positions.

        Args:
            int_list: List of non-negative integers.

        Returns:
            Tuple of (k_main, k_overflow_idx, overflow_indices)
            - k_main: bits for main area values (including overflow flag)
            - k_overflow_idx: bits needed to index overflow array
            - overflow_indices: indices of values going to overflow
        """
        if not int_list:
            return 0, 0, []

        # Sort unique values to find threshold
        sorted_vals = sorted(set(int_list))
        n_unique = len(sorted_vals)

        if n_unique == 1:
            # All same value, no overflow needed
            return sorted_vals[0].bit_length(), 0, []

        # Find threshold at specified percentile
        threshold_idx = int(n_unique * self._overflow_threshold)
        if threshold_idx >= n_unique:
            threshold_idx = n_unique - 1

        threshold_value = sorted_vals[threshold_idx]

        # Find indices of overflow values
        overflow_indices = [i for i, v in enumerate(int_list) if v > threshold_value]

        if not overflow_indices:
            # No overflow needed
            max_val = max(int_list)
            return max_val.bit_length(), 0, []

        # Calculate bits needed
        k_normal = threshold_value.bit_length()  # bits for normal values
        k_overflow_idx = len(overflow_indices).bit_length()  # bits to index overflow
        k_main = k_normal + 1  # +1 for overflow flag bit

        # Check if overflow is actually beneficial
        k_no_overflow = max(int_list).bit_length()
        total_bits_with_overflow = len(int_list) * k_main + len(overflow_indices) * 32
        total_bits_without_overflow = len(int_list) * k_no_overflow

        if total_bits_with_overflow >= total_bits_without_overflow:
            # Overflow not beneficial
            return k_no_overflow, 0, []

        return k_main, k_overflow_idx, overflow_indices

    def compress(self, int_list: list[int]) -> dict:
        """
        Compress using overflow area for large values.

        Args:
            int_list: List of non-negative integers.

        Returns:
            Dictionary with:
            - "k": bit width for main area (includes overflow flag)
            - "k_overflow": bit width for overflow indices
            - "n": number of values
            - "words": list of uint32 words for main area
            - "overflow": list of overflow values
            - "crossing": whether crossing is used

        Raises:
            ValueError: If any value is negative.
        """
        if not int_list:
            return {
                "k": 0,
                "k_overflow": 0,
                "n": 0,
                "words": [],
                "overflow": [],
                "crossing": self._crossing,
            }

        # Validate
        if any(x < 0 for x in int_list):
            raise ValueError("All values must be non-negative")

        n = len(int_list)
        max_val = max(int_list)

        if max_val == 0:
            return {
                "k": 0,
                "k_overflow": 0,
                "n": n,
                "words": [],
                "overflow": [],
                "crossing": self._crossing,
            }

        # Determine overflow strategy
        k_main, k_overflow_idx, overflow_indices = self._determine_overflow_strategy(int_list)

        if not overflow_indices:
            # No overflow, regular compression
            return self._compress_no_overflow(int_list, k_main)

        # Build overflow mapping
        overflow_values = [int_list[i] for i in overflow_indices]
        overflow_map = {idx: pos for pos, idx in enumerate(overflow_indices)}

        # Create encoded array with overflow markers
        encoded = []
        for i, value in enumerate(int_list):
            if i in overflow_map:
                # Mark as overflow: flag=1, followed by overflow index
                overflow_pos = overflow_map[i]
                encoded_val = (1 << (k_main - 1)) | overflow_pos
                encoded.append(encoded_val)
            else:
                # Normal value: flag=0, followed by value
                encoded.append(value)

        # Compress encoded array
        if self._crossing:
            packed_data = self._compress_crossing(encoded, k_main)
        else:
            packed_data = self._compress_noncrossing(encoded, k_main)

        result = {
            "k": k_main,
            "k_overflow": k_overflow_idx,
            "n": n,
            "words": packed_data,
            "overflow": overflow_values,
            "crossing": self._crossing,
        }

        self._pack = result
        return result

    def _compress_no_overflow(self, int_list: list[int], k: int) -> dict:
        """Compress without overflow."""
        if self._crossing:
            data = self._compress_crossing(int_list, k)
        else:
            data = self._compress_noncrossing(int_list, k)

        result = {
            "k": k,
            "k_overflow": 0,
            "n": len(int_list),
            "words": data,
            "overflow": [],
            "crossing": self._crossing,
        }
        self._pack = result
        return result

    def _compress_crossing(self, values: list[int], k: int) -> list[int]:
        """Compress values using crossing method."""
        if k > 32:
            raise ValueError(f"Bit width {k} exceeds 32-bit limit")

        total_bits = len(values) * k
        num_words = (total_bits + 31) // 32
        words = [0] * num_words

        bit_pos = 0
        mask = (1 << k) - 1

        for value in values:
            value &= mask
            word_idx = bit_pos // 32
            bit_offset = bit_pos % 32
            bits_remaining = 32 - bit_offset

            if k <= bits_remaining:
                words[word_idx] |= value << bit_offset
            else:
                lower_bits = value & ((1 << bits_remaining) - 1)
                words[word_idx] |= lower_bits << bit_offset
                upper_bits = value >> bits_remaining
                words[word_idx + 1] |= upper_bits

            bit_pos += k

        return words

    def _compress_noncrossing(self, values: list[int], k: int) -> list[int]:
        """Compress values using non-crossing method."""
        if k > 32:
            raise ValueError(f"Bit width {k} exceeds 32-bit limit")

        capacity = 32 // k
        if capacity == 0:
            raise ValueError(f"Bit width {k} too large for 32-bit words")

        num_words = (len(values) + capacity - 1) // capacity
        words = [0] * num_words
        mask = (1 << k) - 1

        for i, value in enumerate(values):
            word_idx = i // capacity
            slot = i % capacity
            bit_offset = slot * k
            words[word_idx] |= (value & mask) << bit_offset

        return words

    def decompress(self, pack: dict) -> list[int]:
        """
        Decompress packed data including overflow handling.

        Args:
            pack: Dictionary with compression data.

        Returns:
            List of decompressed integers.
        """
        k = pack["k"]
        n = pack["n"]
        words = pack["words"]
        overflow = pack.get("overflow", [])
        crossing = pack.get("crossing", True)

        if n == 0:
            return []

        if k == 0:
            return [0] * n

        # Decompress main area
        if crossing:
            encoded = self._decompress_crossing(words, k, n)
        else:
            encoded = self._decompress_noncrossing(words, k, n)

        # Handle overflow
        if not overflow:
            return encoded

        # Replace overflow markers with actual values
        result = []
        overflow_flag_mask = 1 << (k - 1)
        index_mask = (1 << (k - 1)) - 1

        for val in encoded:
            if val & overflow_flag_mask:
                # Overflow value
                overflow_idx = val & index_mask
                result.append(overflow[overflow_idx])
            else:
                result.append(val)

        return result

    def _decompress_crossing(self, words: list[int], k: int, n: int) -> list[int]:
        """Decompress using crossing method."""
        mask = (1 << k) - 1
        result = []

        for i in range(n):
            bit_offset = i * k
            word_idx = bit_offset // 32
            bit_in_word = bit_offset % 32
            bits_remaining = 32 - bit_in_word

            if k <= bits_remaining:
                value = (words[word_idx] >> bit_in_word) & mask
            else:
                lower_mask = (1 << bits_remaining) - 1
                lower_bits = (words[word_idx] >> bit_in_word) & lower_mask
                upper_bits_count = k - bits_remaining
                upper_mask = (1 << upper_bits_count) - 1
                upper_bits = words[word_idx + 1] & upper_mask
                value = (upper_bits << bits_remaining) | lower_bits

            result.append(value)

        return result

    def _decompress_noncrossing(self, words: list[int], k: int, n: int) -> list[int]:
        """Decompress using non-crossing method."""
        capacity = 32 // k
        mask = (1 << k) - 1
        result = []

        for i in range(n):
            word_idx = i // capacity
            slot = i % capacity
            bit_offset = slot * k
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
            RuntimeError: If compress() not called.
        """
        if self._pack is None:
            raise RuntimeError("Must call compress() before get()")

        n = self._pack["n"]
        if i < 0 or i >= n:
            raise IndexError(f"Index {i} out of bounds for length {n}")

        k = self._pack["k"]
        words = self._pack["words"]
        overflow = self._pack.get("overflow", [])
        crossing = self._pack.get("crossing", True)

        if k == 0:
            return 0

        # Extract encoded value
        if crossing:
            encoded_val = self._get_crossing(words, k, i)
        else:
            encoded_val = self._get_noncrossing(words, k, i)

        # Check for overflow
        if overflow:
            overflow_flag_mask = 1 << (k - 1)
            if encoded_val & overflow_flag_mask:
                index_mask = (1 << (k - 1)) - 1
                overflow_idx = encoded_val & index_mask
                return overflow[overflow_idx]

        return encoded_val

    def _get_crossing(self, words: list[int], k: int, i: int) -> int:
        """Get value using crossing method."""
        bit_offset = i * k
        word_idx = bit_offset // 32
        bit_in_word = bit_offset % 32
        bits_remaining = 32 - bit_in_word
        mask = (1 << k) - 1

        if k <= bits_remaining:
            return (words[word_idx] >> bit_in_word) & mask
        else:
            lower_mask = (1 << bits_remaining) - 1
            lower_bits = (words[word_idx] >> bit_in_word) & lower_mask
            upper_bits_count = k - bits_remaining
            upper_mask = (1 << upper_bits_count) - 1
            upper_bits = words[word_idx + 1] & upper_mask
            return (upper_bits << bits_remaining) | lower_bits

    def _get_noncrossing(self, words: list[int], k: int, i: int) -> int:
        """Get value using non-crossing method."""
        capacity = 32 // k
        word_idx = i // capacity
        slot = i % capacity
        bit_offset = slot * k
        mask = (1 << k) - 1
        return (words[word_idx] >> bit_offset) & mask

    def load(self, pack: dict) -> None:
        """
        Load a previously compressed representation to enable get() operations.

        Args:
            pack: Dictionary with compressed data from compress().
        """
        self._pack = pack
