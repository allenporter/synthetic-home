"""Command to dump out all of the synthetic home device types."""

import argparse
import dataclasses

import yaml

from synthetic_home import device_types


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--device_type",
        type=str,
        help="Limit to only one specific device type",
    )


async def run(args: argparse.Namespace) -> int:
    registry = device_types.load_device_type_registry()
    data = registry.device_types
    if args.device_type is not None:
        device_type = data[args.device_type]
        data = {device_type.device_type: data[args.device_type]}
    dict_data = {k: dataclasses.asdict(v) for k, v in data.items()}
    yaml_dump = yaml.dump(dict_data, sort_keys=False)
    print(yaml_dump)
    return 0
