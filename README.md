# Bit Packing - Integer Array Compression

**Author:** Marouane BENABDELKADER
**Course:** Software Engineering 2025
**Project:** Data Compression for Speed-Up Transmission

**📄 [View Full Report (PDF)](bitpacking.pdf)**

Integer-array compression with direct random access using bit packing techniques.

## Project Overview

This project implements three variants of bit packing compression:

1. **Non-crossing**: Values don't span 32-bit word boundaries
2. **Crossing**: Values can span boundaries for optimal compression
3. **Overflow**: Two-tier storage for arrays with outliers

All implementations maintain O(1) random access to compressed elements.

## Features

- Three bit packing algorithms with different trade-offs
- Direct random access without full decompression (O(1) access via `load()` method)
- **Interactive mode** for guided exploration of bit packing
- **Enhanced CLI output** showing detailed compression/decompression results
- Comprehensive benchmarking suite
- Transmission time analysis
- Command-line interface with all implementations available
- Factory pattern for algorithm selection
- Full test coverage (69 tests)

## Requirements

- Python 3.11 or higher
- pip package manager
- (Optional) Conda for environment management

## Installation Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/MarouaneBenabdelkader/bitpacking.git
cd bitpacking
```

### Step 2: Create Python Environment

#### Option A: Using Conda (Recommended)

```bash
# Create conda environment with Python 3.11
conda create -n bitpacking python=3.11

# Activate the environment
conda activate bitpacking
```

#### Option B: Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

### Step 3: Install the Package

```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"
```

This will install:

- The `bitpacking` package
- pytest (for testing)
- black (for code formatting)
- ruff (for linting)

### Step 4: Verify Installation

```bash
# Check that the command-line tool is available
bitpacking --help

# Should display usage information for all commands:
# - compress, decompress, get: File operations
# - bench: Performance benchmarks
# - interactive: Interactive guided mode
# - transmission: Network analysis
```

## Running Tests

### Run All Tests

```bash
# From the project root directory
pytest tests/

# Expected output:
# ============================= test session starts ==============================
# collected 69 items
# tests/test_cross.py ......................                               [ 31%]
# tests/test_noncross.py ...................                               [ 59%]
# tests/test_overflow.py .................                                 [ 84%]
# tests/test_transmission.py ...........                                   [100%]
# ============================== 69 passed in 0.20s ==============================
```

### Run Specific Test Files

```bash
# Test non-crossing implementation (19 tests)
pytest tests/test_noncross.py -v

# Test crossing implementation (22 tests)
pytest tests/test_cross.py -v

# Test overflow implementation (17 tests)
pytest tests/test_overflow.py -v

# Test transmission analysis (11 tests)
pytest tests/test_transmission.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=bitpacking --cov-report=html
```

## Usage Examples

### Command Line Interface

The CLI now provides enhanced output showing detailed compression/decompression results.

**Note**: Example JSON files are organized in the `examples/` folder. Test files used during development are in `test_files/`.

#### 1. Compress an Array

```bash
# Create input file (use Python to ensure proper JSON formatting)
python -c "import json; json.dump([1, 5, 3, 7, 2, 8, 4, 6, 9, 10], open('examples/input.json', 'w'))"

# Compress with non-crossing (default)
bitpacking compress --in examples/input.json --out examples/compressed.json
# Output:
# [OK] Compression successful!
#   Input: examples/input.json
#   Output: examples/compressed.json
#   Original data: [1, 5, 3, 7, 2, 8, 4, 6, 9, 10]
#   Number of values (n): 10
#   Bits per value (k): 4
#   Storage words: 2
#   Compressed words: [1686270801, 169]

# Compress with crossing (better compression)
bitpacking -i cross compress --in examples/input.json --out examples/compressed.json

# Compress with overflow (best for skewed data)
bitpacking -i overflow compress --in examples/input.json --out examples/compressed.json
```

#### 2. Decompress an Array

```bash
bitpacking decompress --in examples/compressed.json --out examples/output.json
# Output:
# [OK] Decompression successful!
#   Input: examples/compressed.json
#   Output: examples/output.json
#   Decompressed data: [1, 5, 3, 7, 2, 8, 4, 6, 9, 10]
#   Number of values: 10
```

#### 3. Random Access (Get Element)

```bash
# Get element at index 3
bitpacking get --in examples/compressed.json --index 3
# Output: 7
```

#### 4. Interactive Mode

The interactive mode provides a guided experience for exploring bit packing:

```bash
# Launch interactive mode
bitpacking interactive
```

The interactive mode will:

1. Ask you to choose an implementation (noncross, cross, overflow, overflow-noncross)
2. Present a menu with options:
   - **Compress**: Enter space-separated integers to compress
   - **Decompress**: View the decompressed data and verify correctness
   - **Get**: Retrieve a value at a specific index
   - **Exit**: Quit the interactive mode

Example session:

```
============================================================
BitPacking Interactive Mode
============================================================

Available implementations:
  1. noncross         - Non-crossing boundaries
  2. cross            - Crossing boundaries allowed
  3. overflow         - Two-tier with overflow (crossing)
  4. overflow-noncross- Two-tier with overflow (non-crossing)

Select implementation (1-4): 3

[OK] Using 'overflow' implementation
============================================================

Options:
  1. Compress data
  2. Decompress (show last compressed data)
  3. Get value at index
  4. Exit

Enter your choice (1-4): 1
Enter integers separated by spaces: 100 200 65000 300 400

[OK] Compression successful!
  Original data: [100, 200, 65000, 300, 400]
  Number of values (n): 5
  Bits per value (k): 16
  Storage words: 3
  Compressed words: [13107300, 19725800, 400]
```

#### 5. Run Benchmarks

```bash
# Benchmark any implementation
bitpacking bench                    # non-crossing (default)
bitpacking -i cross bench          # crossing
bitpacking -i overflow bench       # overflow with crossing
bitpacking -i overflow-noncross bench  # overflow without crossing
```

Output includes:

- Compression time (median and p95)
- Decompression time (median and p95)
- Random access time (median and p95)
- Compression ratio

#### 6. Transmission Time Analysis

```bash
# Analyze when compression is beneficial (all parameters on one line for easy copy-paste)
bitpacking transmission --uncompressed-bits 320000 --compressed-bits 80000 --compression-time 1000000 --decompression-time 500000

# Or analyze from an existing compressed file
bitpacking transmission --file examples/compressed.json

# Shows analysis for different network speeds:
# - 10 Gbps LAN
# - 1 Gbps LAN  
# - 100 Mbps
# - 10 Mbps
# - 1 Mbps
# - 56 Kbps modem
```

### Python API

```python
from bitpacking import BitPackingNonCross, BitPackingCrossed, BitPackingOverflow

# Example 1: Non-crossing implementation
bp = BitPackingNonCross()
data = [1, 5, 3, 7, 2, 8, 4, 6]
packed = bp.compress(data)

# Random access without decompression
value = bp.get(3)  # O(1) access to index 3
print(f"Value at index 3: {value}")  # Output: 7

# Full decompression
restored = bp.decompress(packed)
assert restored == data

# Example 2: Crossing implementation (better compression)
bp_cross = BitPackingCrossed()
packed_cross = bp_cross.compress(data)
print(f"Compressed to {len(packed_cross['words'])} words")

# Example 3: Overflow implementation (best for skewed data)
bp_overflow = BitPackingOverflow(crossing=True, overflow_threshold=0.95)
data_with_outliers = [1, 2, 3, 1024, 4, 5, 2048]
packed_overflow = bp_overflow.compress(data_with_outliers)
print(f"Overflow compression: {len(packed_overflow['words'])} words")
print(f"Overflow items: {len(packed_overflow.get('overflow', []))}")

# Example 4: Factory pattern
from bitpacking import get_bitpacking
bp = get_bitpacking("overflow-cross", overflow_threshold=0.9)
packed = bp.compress(data)

# Example 5: Transmission time analysis
from bitpacking import TransmissionMetrics

metrics = TransmissionMetrics(
    uncompressed_size_bits=len(data) * 32,
    compressed_size_bits=len(packed['words']) * 32,
    compression_time_ns=1_000_000,  # 1ms
    decompression_time_ns=500_000,   # 0.5ms
    bandwidth_bps=1e6,               # 1 Mbps
    latency_ns=10_000_000            # 10ms
)

print(f"Compression beneficial: {metrics.is_compression_beneficial}")
print(f"Time saved: {metrics.time_saved_ns / 1e6:.2f} ms")
print(metrics.format_report())
```

## Project Structure

```
bitpacking/
├── src/bitpacking/
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # CLI entry point
│   ├── base.py              # Abstract interface
│   ├── noncross.py          # Non-crossing implementation
│   ├── cross.py             # Crossing implementation
│   ├── overflow.py          # Overflow implementation
│   ├── factory.py           # Factory pattern
│   ├── cli.py               # Command-line interface
│   ├── bench.py             # Benchmarking utilities
│   └── transmission.py      # Transmission analysis
├── tests/
│   ├── test_noncross.py     # 19 tests
│   ├── test_cross.py        # 22 tests
│   ├── test_overflow.py     # 17 tests
│   └── test_transmission.py # 11 tests
├── examples/                # Example JSON files
│   └── .gitkeep            # (JSON files gitignored)
├── test_files/              # Test JSON files
│   └── .gitkeep            # (JSON files gitignored)
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── bitpacking.pdf           # Academic report (PDF)
```

## Algorithms

### 1. Non-Crossing Bit Packing

**Description**: Values are packed into 32-bit words without crossing boundaries.

**Algorithm**:

1. Determine k = minimum bits needed for maximum value
2. Calculate capacity per word: `capacity = 32 // k`
3. Pack values sequentially within word boundaries
4. Some padding bits are wasted at boundaries

**Complexity**: O(n) compress, O(n) decompress, O(1) get

**Use case**: Fastest operations, predictable performance

### 2. Crossing Bit Packing

**Description**: Values can span word boundaries for optimal space utilization.

**Algorithm**:

1. Determine k = minimum bits needed
2. Pack values sequentially across all words
3. Values may span two consecutive words
4. No wasted bits (total = n × k bits exactly)

**Complexity**: O(n) compress, O(n) decompress, O(1) get

**Use case**: Best compression ratio, slightly slower than non-crossing

### 3. Overflow Bit Packing

**Description**: Two-tier storage for arrays with outliers.

**Algorithm**:

1. Calculate threshold (default: 95th percentile)
2. Determine k_main = bits for threshold value + 1 flag bit
3. Values ≤ threshold stored in main array
4. Larger values stored in separate overflow array
5. Flag bit indicates main (0) or overflow (1) storage

**Example**:

- Input: `[1, 2, 3, 1024, 4, 5, 2048]`
- Without overflow: 11 bits × 7 = 77 bits
- With overflow: 4 bits × 7 + 11 bits × 2 = 50 bits
- Savings: 35% reduction

**Complexity**: O(n log n) compress (sorting), O(n) decompress, O(1) get

**Use case**: Arrays with skewed distributions and outliers

## Benchmarks

Run the comprehensive benchmark suite:

```bash
# Generate full benchmark report
python generate_report.py
```

This creates `REPORT.md` with detailed performance analysis including:

- Compression ratios for each implementation
- Timing measurements (compress, decompress, get operations)
- Network scenario analysis
- When compression is worthwhile vs. transmission costs

## Transmission Time Analysis

The project includes analysis to determine when compression reduces total transmission time:

**Formula**:

```
T_uncompressed = latency + (uncompressed_size / bandwidth)
T_compressed = latency + compress_time + (compressed_size / bandwidth) + decompress_time

Compression is beneficial when: T_compressed < T_uncompressed
```

**Key findings** (for typical scenario):

- **Fast networks (>1 Gbps)**: Compression overhead exceeds savings
- **Medium networks (10-100 Mbps)**: Compression starts to help
- **Slow networks (<10 Mbps)**: Compression provides significant speedup

## Academic Report

📄 **[Full Report (PDF)](bitpacking.pdf)** - Comprehensive academic report covering all aspects of the project.

The report includes:

- Problem description and motivation
- Software architecture with diagrams
- Design patterns (Factory, Strategy, Template Method)
- Separation of concerns analysis
- Algorithm descriptions with pseudocode
- Complexity analysis
- Performance benchmarks
- Transmission time modeling
- Testing methodology
- Code listings

## Code Quality

The project follows best practices:

```bash
# Run code formatter
black src/ tests/

# Run linter
ruff check src/ tests/

# Run type checker (if mypy installed)
mypy src/

# All quality checks should pass
```

## Troubleshooting

### Issue: `bitpacking: command not found`

**Solution**: Ensure package is installed and environment is activated

```bash
conda activate bitpacking
pip install -e ".[dev]"
```

### Issue: Tests fail with import errors

**Solution**: Install package in development mode

```bash
pip install -e ".[dev]"
```

## Author

**Marouane BENABDELKADER**
Software Engineering Course 2025
Project: Data Compression for Speed-Up Transmission

## Contact

For questions or issues:

- GitHub Issues: https://github.com/MarouaneBenabdelkader/bitpacking/issues
- Email: (available upon request)

## Acknowledgments

This project was developed as part of the Software Engineering course 2025, demonstrating:

- Algorithm design and implementation
- Software architecture patterns
- Performance analysis and optimization
- Comprehensive testing practices
- Technical documentation
