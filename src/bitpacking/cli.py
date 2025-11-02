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

    print("\n[OK] Compression successful!")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Original data: {data}")
    print(f"  Number of values (n): {len(data)}")
    print(f"  Bits per value (k): {packed['k']}")
    print(f"  Storage words: {len(packed['words'])}")
    print(f"  Compressed words: {packed['words']}")
    if 'overflow' in packed and packed['overflow']:
        print(f"  Overflow entries: {len(packed['overflow'])}")
        print(f"  Overflow indices: {list(packed['overflow'].keys())}")


def cmd_decompress(args):
    """Decompress a packed array to JSON file."""
    with open(args.input) as f:
        packed = json.load(f)

    bp = get_bitpacking(args.implementation)
    data = bp.decompress(packed)

    with open(args.output, "w") as f:
        json.dump(data, f)

    print("\n[OK] Decompression successful!")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Decompressed data: {data}")
    print(f"  Number of values: {len(data)}")


def cmd_get(args):
    """Get element at index from packed array."""
    with open(args.input) as f:
        packed = json.load(f)

    bp = get_bitpacking(args.implementation)
    bp.load(packed)

    try:
        value = bp.get(args.index)
        print(value)
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_bench(args):
    """Run benchmarks."""
    run_benchmarks(args.implementation)


def cmd_interactive(args):
    """Run interactive guided mode."""
    print("=" * 60)
    print("BitPacking Interactive Mode")
    print("=" * 60)

    # Ask user to choose implementation
    print("\nAvailable implementations:")
    print("  1. noncross         - Non-crossing boundaries")
    print("  2. cross            - Crossing boundaries allowed")
    print("  3. overflow         - Two-tier with overflow (crossing)")
    print("  4. overflow-noncross- Two-tier with overflow (non-crossing)")

    while True:
        impl_choice = input("\nSelect implementation (1-4): ").strip()
        if impl_choice == "1":
            implementation = "noncross"
            break
        elif impl_choice == "2":
            implementation = "cross"
            break
        elif impl_choice == "3":
            implementation = "overflow"
            break
        elif impl_choice == "4":
            implementation = "overflow-noncross"
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

    bp = get_bitpacking(implementation)
    last_pack = None
    last_data = None

    print(f"\n[OK] Using '{implementation}' implementation")
    print("=" * 60)

    while True:
        print("\nOptions:")
        print("  1. Compress data")
        print("  2. Decompress (show last compressed data)")
        print("  3. Get value at index")
        print("  4. Exit")

        try:
            choice = input("\nEnter your choice (1-4): ").strip()

            if choice == "1":
                # Compress
                numbers_input = input("Enter integers separated by spaces: ").strip()
                try:
                    numbers = [int(x) for x in numbers_input.split()]
                    if not numbers:
                        print("Error: Please enter at least one number.")
                        continue

                    last_data = numbers
                    last_pack = bp.compress(numbers)
                    bp.load(last_pack)

                    print("\n[OK] Compression successful!")
                    print(f"  Original data: {numbers}")
                    print(f"  Number of values (n): {last_pack['n']}")
                    print(f"  Bits per value (k): {last_pack['k']}")
                    print(f"  Storage words: {len(last_pack['words'])}")
                    print(f"  Compressed words: {last_pack['words']}")
                    if 'overflow' in last_pack and last_pack['overflow']:
                        print(f"  Overflow entries: {len(last_pack['overflow'])}")
                        print(f"  Overflow indices: {list(last_pack['overflow'].keys())}")
                except ValueError:
                    print("Error: Invalid input. Please enter integers only.")
                except Exception as e:
                    print(f"Error during compression: {e}")

            elif choice == "2":
                # Decompress
                if last_pack is None:
                    print("Error: You must compress data first.")
                    continue

                try:
                    result = bp.decompress(last_pack)
                    print("\n[OK] Decompression successful!")
                    print(f"  Decompressed data: {result}")
                    if last_data:
                        if result == last_data:
                            print("  [OK] Matches original data")
                        else:
                            print("  [!] WARNING: Does not match original!")
                except Exception as e:
                    print(f"Error during decompression: {e}")

            elif choice == "3":
                # Get
                if last_pack is None:
                    print("Error: You must compress data first.")
                    continue

                try:
                    max_index = last_pack['n'] - 1
                    index_input = input(f"Enter index (0 to {max_index}): ").strip()
                    index = int(index_input)
                    value = bp.get(index)
                    print(f"\n[OK] Value at index {index}: {value}")
                    if last_data and 0 <= index < len(last_data):
                        print(f"  (Original value: {last_data[index]})")
                except ValueError:
                    print("Error: Invalid index. Please enter an integer.")
                except IndexError as e:
                    print(f"Error: {e}")
                except Exception as e:
                    print(f"Error: {e}")

            elif choice == "4":
                # Exit
                print("\nExiting interactive mode. Goodbye!")
                break

            else:
                print("Error: Invalid choice. Please enter 1, 2, 3, or 4.")

        except KeyboardInterrupt:
            print("\n\nExiting interactive mode. Goodbye!")
            break
        except EOFError:
            print("\n\nExiting.")
            break


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
        choices=["noncross", "cross", "overflow", "overflow-cross", "overflow-noncross"],
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

    # Interactive command
    subparsers.add_parser("interactive", help="Interactive guided mode")

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
    elif args.command == "interactive":
        cmd_interactive(args)
    elif args.command == "transmission":
        cmd_transmission(args)


if __name__ == "__main__":
    main()
