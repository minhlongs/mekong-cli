"""Mekong SDK CLI - Command line interface."""

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Run the mekong-sdk CLI main entry point.

    Usage:
        mekong-sdk --version
        mekong-sdk --help
    """
    parser = argparse.ArgumentParser(
        prog="mekong-sdk",
        description="Mekong SDK Command Line Interface",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show version and exit",
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Show SDK information",
    )

    args = parser.parse_args(argv)

    if args.info:
        print("Mekong SDK v0.1.0")
        print("Python SDK for Mekong CLI API")
        print("Docs: https://github.com/longtho638-jpg/mekong-cli")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
