# synthetic-home

Library for managing synthetic home device registry. This project is primarily
used by the [home-assistant-synthetic-home](https://github.com/allenporter/home-assistant-synthetic-home)
custom component and the [home-assistant-datasets](https://github.com/allenporter/home-assistant-datasets)
which creates instances of synthetic homes.

See the [synthetic_home/registry](synthetic_home/registry) for details on the registry.

## Example

This is an example of a synthetic hoome configuration file:

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

## Device Type Registry

A device type is a definition of a type of physical device in a smart home. A
device may additionally be represented by multiple entities. For example, a
`climate-hvac` device may be represented by a *climate entity* and a *temperature
sensor entity*.

### Device types

Device types are defined to represent common configured household devices,
but may not support every single feature in the smart home. That is, these
are meant to be representative, but not necessarily exhaustive.

Each file in `synthetic_home/registry` directory contains a device type name. New device
types may be added as new use cases are needed.

### Entities

Entities are specified by platform, where each value is an entity description
key defined in the code somewhere. That is, adding a new entity type requires
it being implemented somewhere in the smart home (e.g. `home-assistant-synthetic-home` custom component).

### Device State

A device type defines `device_states` that can support a pre-defined states that
can be used for testing and evaluating the other systems using synthetic entities.

For example: When testing an HVAC device there are many different state attributes
but there may only be a few _interesting_ states to evaluate such as:

- The device is not running
- The device target temperature is set to a normal range
- The device target temperature is set to an abnormal range

We use the pre-canned device states to simplify data generation to not need
to consider every possibibility. This is implemented effectively as if setting
these attributes in the config file.

### Device State Example

You can set a `device_state` inline in the home. A `motion-sensor` devices three
states by default `on`, `off`, and `battery-low`.  Be careful for special yaml
truthy values, hence the value below is in quotes:

```yaml
---
name: Family Farmhouse
devices:
  Front Yard:
    - name: Front Yard Motion
      device_type: motion-sensor
      device_state: "on"
```
