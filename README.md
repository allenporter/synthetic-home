# synthetic-home

Library for generating synthetic homes, devices, and entities. This project is primarily
used by the [home-assistant-synthetic-home](https://github.com/allenporter/home-assistant-synthetic-home)
custom component that can make a home out of an inventory and the [home-assistant-datasets](https://github.com/allenporter/home-assistant-datasets)
which creates instances of synthetic homes and devices.

## Overview

### Home

A home contains a definition of home with areas and devices. This example home is
called *Family Farmhouse* with two devices in the *Kitchen*.

```yaml
---
name: Family Farmhouse
devices:
  Kitchen:
    - name: Light
      device_type: light-dimmable
    - name: Coffe Maker
      device_type: smart-plug
      device_info:
        manufacturer: Shelly
```

### Device Registry

The above devices are of type *light-dimmable* and *smart-plug*. These device types
are defined in a *Device Registry* that maps a higher level device type into lower
level entities. For example, a *smart-plug* device is represented by a *switch*
and a *sensor* that measures power draw. A device can also define device states
which are mapped to the individual entity states.

The [home-assistant-datasets](https://github.com/allenporter/home-assistant-datasets) project
uses an LLM to create devices within a home without having to worry about the lower
level details of entities and attributes.

See the [synthetic_home/registry](synthetic_home/registry) for details on the registry.

### Device types

Device types are defined to represent common configured household devices,
but may not support every single feature in the smart home. That is, these
are meant to be representative, but not necessarily exhaustive.

Each file in `synthetic_home/registry` directory contains a device type name. New device
types may be added as new use cases are needed.

### Inventory

An inventory is set of devies, areas, and most importantly individual *Entities*, and a default state and set of attributes.  An inventory can be used by [home-assistant-synthetic-home](https://github.com/allenporter/home-assistant-synthetic-home) to actually load a Home Assistant instance with these
areas, devices, and entities.

```yaml
---
areas:
- name: Family room
  id: family_room
devices:
- name: Floor Lamp
  id: floor_lamp
  area: family_room
  info:
    manufacturer: Wyze
entities:
- name: Floor Lamp Energy
  id: sensor.floor_lamp_energy
  area: family_room
  device: floor_lamp
  state: '1'
  attributes:
    device_class: sensor.SensorDeviceClass.ENERGY
    state_class: sensor.SensorStateClass.TOTAL_INCREASING
    native_unit_of_measurement: kWh
- name: Floor Lamp
  id: switch.floor_lamp
  area: family_room
  device: floor_lamp
  state: true
  attributes:
    device_class: switch.SwitchDeviceClass.OUTLET
```

## Inventory Creation

There are multiple ways to create an inventory.

### Export from Home Assistant

You can create a synthetic home inventory copied from an existing home assistant
instance. You need to create an access token and export an inventory like this:

```bash
$ HASS_URL="http://home-assistant.home-assistant:8123"
$ API_TOKEN="XXXXXXXXXXX"
$ synthetic-home --debug export_inventory "${HASS_URL}" "${API_TOKEN}" > inventory.yaml
```

### Manual Inventory

You can manually create an inventory by hand, but even better is to use a home definition
for a set of devies. See [home-asssistant-datasets](https://github.com/allenporter/home-assistant-datasets)
for some existing repos of synthetic homes created by an LLM. Or create one yourself based on
devices you want to test defined in the device registry. Given an example `famhouse-home.yaml`:

```yaml
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
  Entry:
    - name: Front Door
      device_type: smart-lock
  Kitchen:
    - name: Light
      device_type: light-dimmable
    - name: Coffe Maker
      device_type: smart-plug
      device_info:
        manufacturer: Shelly
  Master Bedroom:
    - name: Bedroom Light
      device_type: light-dimmable
    - name: Bedroom Blinds
      device_type: smart-blinds
      device_info:
        model: RollerBlinds
        manufacturer: Motion Blinds
        sw_version: 1.1.0
    - name: Bedroom Window
      device_type: window-sensor
  Garage:
    - name: Garage Door
      device_type: garage-door
  Front Yard:
    - name: Front motion
      device_type: motion-sensor
```

You can export an inventory file:

```bash
$ synthetic-home create_inventory famhouse-home.yaml > inventory.yaml
```

This can then be loaded into a [home-assistants-synthetic-home](https://github.com/allenporter/home-assistant-synthetic-home/) custom component.
