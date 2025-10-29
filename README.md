# bitpacking

Integer-array compression with direct random access.

## Features

- **Non-crossing bit packing**: Fixed bit-width compression that doesn't cross 32-bit word boundaries
- **Crossing bit packing**: Optimal space compression where values can span word boundaries
- **Direct random access**: O(1) element retrieval without decompression
- **CLI tools**: Compress, decompress, and query compressed arrays
- **Benchmarking**: Performance testing harness

## Installation

```bash
# Create conda environment
conda create -n bitpacking python=3.11
conda activate bitpacking

# Install in development mode
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Compress an array (default: non-crossing)
bitpacking compress --in input.json --out compressed.json

# Use crossing implementation for better compression
bitpacking -i cross compress --in input.json --out compressed.json

# Decompress
bitpacking decompress --in compressed.json --out output.json

# Get element at index
bitpacking get --in compressed.json --index 42

# Run benchmarks (specify implementation)
bitpacking bench              # noncross (default)
bitpacking -i cross bench     # crossing
```

### Python API

```python
from bitpacking import BitPackingNonCross, BitPackingCrossed

# Non-crossing implementation
bp = BitPackingNonCross()
data = [1, 5, 3, 7, 2, 8, 4, 6]
packed = bp.compress(data)

# Random access
value = bp.get(3)  # O(1) access to index 3

# Decompress
restored = bp.decompress(packed)
assert restored == data

# Crossing implementation (better compression)
bp_cross = BitPackingCrossed()
packed_cross = bp_cross.compress(data)
# Typically uses fewer words than non-crossing
```

## Running Tests

```bash
pytest tests/
```

## Running Benchmarks

```bash
bitpacking bench              # Benchmark non-crossing
bitpacking -i cross bench     # Benchmark crossing
# Outputs JSON lines with performance metrics
```

## Algorithms

### Non-Crossing Bit Packing

The non-crossing implementation:

- Uses fixed bit-width `k` = minimum bits needed for max value
- Packs values into 32-bit words without crossing boundaries
- Capacity per word = 32 // k
- Enables fast random access: O(1) get operations
- Trade-off: Some bits wasted due to alignment padding

### Crossing Bit Packing

The crossing implementation:

- Uses fixed bit-width `k` = minimum bits needed for max value
- Values can span across two consecutive 32-bit words
- Optimal space usage: total bits = n × k exactly (no wasted bits)
- O(1) random access with bit offset calculation
- Slightly more complex bit manipulation for read/write
- Trade-off: Better compression, slightly slower access

### Performance Comparison

For 10,000 values with k=7 bits:
- **Non-crossing**: Uses 25 words (800 bits wasted)
- **Crossing**: Uses 22 words (no wasted bits)

## TODO

- [x] Crossing bit packing (higher compression)
- [ ] Overflow handling for large value ranges
- [ ] Additional compression schemes
