"""Command-line interface for bitpacking."""

import argparse
import json
import sys

from bitpacking.bench import run_benchmarks
from bitpacking.factory import get_bitpacking
from bitpacking.transmission import analyze_scenarios


def cmd_compress(args):
    """Compress an array from JSON file."""
    with open(args.input) as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: Input must be a JSON array of integers", file=sys.stderr)
        sys.exit(1)

    bp = get_bitpacking(args.implementation)
    packed = bp.compress(data)

    with open(args.output, "w") as f:
        json.dump(packed, f)

    print(f"Compressed {len(data)} values to {args.output}")
    print(f"k={packed['k']} bits, {len(packed['words'])} words")


def cmd_decompress(args):
    """Decompress a packed array to JSON file."""
    with open(args.input) as f:
        packed = json.load(f)

    bp = get_bitpacking(args.implementation)
    data = bp.decompress(packed)

    with open(args.output, "w") as f:
        json.dump(data, f)

    print(f"Decompressed {len(data)} values to {args.output}")


def cmd_get(args):
    """Get element at index from packed array."""
    with open(args.input) as f:
        packed = json.load(f)

    bp = get_bitpacking(args.implementation)
    bp.compress([])  # Initialize with empty to set up state
    bp._pack = packed  # Set the pack directly

    try:
        value = bp.get(args.index)
        print(value)
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_bench(args):
    """Run benchmarks."""
    run_benchmarks(args.implementation)


def cmd_transmission(args):
    """Analyze transmission scenarios."""
    if args.file:
        # Load compressed data from file and analyze
        with open(args.file) as f:
            packed = json.load(f)

        # Estimate sizes
        compressed_size_bits = len(packed["words"]) * 32
        # Original size estimation: n values * k bits (assuming same k for all)
        n = packed.get("n", 0)
        packed.get("k", 0)
        uncompressed_size_bits = n * 32  # Assume 32-bit integers

        # Use default timing if not provided
        compression_time_ns = args.compression_time or 1_000_000  # 1ms default
        decompression_time_ns = args.decompression_time or 500_000  # 0.5ms default

        print(
            analyze_scenarios(
                uncompressed_size_bits,
                compressed_size_bits,
                compression_time_ns,
                decompression_time_ns,
            )
        )
    else:
        # Use provided parameters
        if (
            args.uncompressed_bits is None
            or args.compressed_bits is None
            or args.compression_time is None
            or args.decompression_time is None
        ):
            print(
                "Error: Must provide --file or all of --uncompressed-bits, "
                "--compressed-bits, --compression-time, --decompression-time",
                file=sys.stderr,
            )
            sys.exit(1)

        print(
            analyze_scenarios(
                args.uncompressed_bits,
                args.compressed_bits,
                args.compression_time,
                args.decompression_time,
            )
        )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Integer array compression with random access")
    parser.add_argument(
        "--implementation",
        "-i",
        default="noncross",
        choices=["noncross", "cross"],
        help="Bit packing implementation to use",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Compress command
    compress_parser = subparsers.add_parser("compress", help="Compress an array")
    compress_parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    compress_parser.add_argument(
        "--out", dest="output", required=True, help="Output compressed JSON file"
    )

    # Decompress command
    decompress_parser = subparsers.add_parser("decompress", help="Decompress a packed array")
    decompress_parser.add_argument(
        "--in", dest="input", required=True, help="Input compressed JSON file"
    )
    decompress_parser.add_argument("--out", dest="output", required=True, help="Output JSON file")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get element at index")
    get_parser.add_argument("--in", dest="input", required=True, help="Input compressed JSON file")
    get_parser.add_argument("--index", type=int, required=True, help="Index of element to retrieve")

    # Bench command
    subparsers.add_parser("bench", help="Run benchmarks")

    # Transmission analysis command
    trans_parser = subparsers.add_parser("transmission", help="Analyze transmission time scenarios")
    trans_parser.add_argument("--file", help="Compressed JSON file to analyze")
    trans_parser.add_argument("--uncompressed-bits", type=int, help="Uncompressed size in bits")
    trans_parser.add_argument("--compressed-bits", type=int, help="Compressed size in bits")
    trans_parser.add_argument(
        "--compression-time", type=int, help="Compression time in nanoseconds"
    )
    trans_parser.add_argument(
        "--decompression-time", type=int, help="Decompression time in nanoseconds"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handler
    if args.command == "compress":
        cmd_compress(args)
    elif args.command == "decompress":
        cmd_decompress(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "bench":
        cmd_bench(args)
    elif args.command == "transmission":
        cmd_transmission(args)


if __name__ == "__main__":
    main()
