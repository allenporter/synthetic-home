"""Script to create inventory files from a synthetic home device file."""

import argparse
import pathlib
import dataclasses

import yaml

from synthetic_home import synthetic_home


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "config_file",
        type=str,
        help="Specifies the synthetic home config file.",
    )


def run(args: argparse.Namespace) -> int:
    home = synthetic_home.load_synthetic_home(pathlib.Path(args.config_file))
    inventory = synthetic_home.build_inventory(home)
    yaml_dump = yaml.dump(dataclasses.asdict(inventory), sort_keys=False)
    print(yaml_dump)
    return 0
