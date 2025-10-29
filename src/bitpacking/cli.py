"""Command-line interface for bitpacking."""

import argparse
import json
import sys

from bitpacking.bench import run_benchmarks
from bitpacking.factory import get_bitpacking


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


if __name__ == "__main__":
    main()
