"""Create inventory files from a synthetic home device file.

Given a home yaml file:

```
---
name: Family Farmhouse
devices:
  Family Room:
    - name: Family Room Lamp
      device_type: light
      device_info:
        manufacturer: Phillips
        model: Hue
    - name: Family Room
      device_type: hvac
      device_info:
        manufacturer: Nest
        sw_version: 1.0.0
      attributes:
        unit_of_measurement: °F
        current_temperature: 60
    - name: Left Window
      device_type: window-sensor
    - name: Right Window
      device_type: window-sensor
```

The `create_inventory` command can convert it to an inventory file which can be
used with the synthetic home custom component.

```bash
$ synthetic-home create_inventory famhouse-home.yaml > famhouse-inventory.yaml
```
"""

import argparse
import pathlib

from synthetic_home import synthetic_home


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "config_file",
        type=str,
        help="Specifies the synthetic home config file.",
    )


async def run(args: argparse.Namespace) -> int:
    home = synthetic_home.load_synthetic_home(pathlib.Path(args.config_file))
    inventory = synthetic_home.build_inventory(home)
    print(inventory.yaml())
    return 0
