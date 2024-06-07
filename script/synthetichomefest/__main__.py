"""Helper scripts for synthetic home."""

import argparse
import importlib
import sys
from pathlib import Path
from typing import cast

from . import list_device_types, create_inventory


def get_base_arg_parser() -> argparse.ArgumentParser:
    """Get a base argument parser."""
    parser = argparse.ArgumentParser(description="Synthetic Home Utility")
    parser.add_argument("--debug", action="store_true", help="Enable log output")
    subparsers = parser.add_subparsers(dest="action", help="Action", required=True)
    create_inventory.create_arguments(
        subparsers.add_parser(
            "create_inventory",
        )
    )
    list_device_types.create_arguments(
        subparsers.add_parser(
            "list_device_types",
        )
    )
    return parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    return get_base_arg_parser().parse_known_args()[0]


def main() -> int:
    """Run a translation script."""
    if not Path("requirements_dev.txt").is_file():
        print("Run from project root")
        return 1

    args = get_arguments()
    module = importlib.import_module(f".{args.action}", "script.synthetichomefest")
    return cast(int, module.run(args))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print()
        print("Aborted!")
        sys.exit(2)
