# bitpacking

Integer-array compression with direct random access.

## Features

- **Non-crossing bit packing**: Fixed bit-width compression that doesn't cross 32-bit word boundaries
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
# Compress an array
bitpacking compress --in input.json --out compressed.json

# Decompress
bitpacking decompress --in compressed.json --out output.json

# Get element at index
bitpacking get --in compressed.json --index 42

# Run benchmarks
bitpacking bench
```

### Python API

```python
from bitpacking import BitPackingNonCross

# Compress
bp = BitPackingNonCross()
data = [1, 5, 3, 7, 2, 8, 4, 6]
packed = bp.compress(data)

# Random access
value = bp.get(3)  # O(1) access to index 3

# Decompress
restored = bp.decompress(packed)
assert restored == data
```

## Running Tests

```bash
pytest tests/
```

## Running Benchmarks

```bash
bitpacking bench
# Outputs JSON lines with performance metrics
```

## Algorithm: Non-Crossing Bit Packing

The non-crossing implementation:

- Uses fixed bit-width `k` = minimum bits needed for max value
- Packs values into 32-bit words without crossing boundaries
- Capacity per word = 32 // k
- Enables fast random access: O(1) get operations

## TODO

- [ ] Crossing bit packing (higher compression)
- [ ] Overflow handling for large value ranges
- [ ] Additional compression schemes
