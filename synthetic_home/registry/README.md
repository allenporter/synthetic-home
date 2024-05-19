# Device Type Registry

A device type is a definition of a type of physical device in a smart home. A
device may additionally be represented by multiple entities. For example, a
climate-hvac device may be represented by a climate entity and a temperature
sensor entity.

## Device types

Device types are defined to represent common configured household devices,
but may not support every single feature in the smart home. That is, these
are meant to be representative, but not necessarily exhaustive.

Each file in this directory contains a device type name. New device types
may be added as new use cases are needed.

## Entities

Entities are specified by platform, where each value is an entity description
key defined in the code. That is, adding a new enttiy type requires adding a
new entity description.

Entities can have attributes like `device_class` or `unit_of_measure` that can
vary for any particular instantiation of that entity for a device.

## Device States

A device type can define `device_states` that can support a pre-canned
restorable states that can be used for testing and evaluating the other systems
using synthetic entities.

For example: When testing an HVAC device there are many different state attributes
but there may only be a few _interesting_ states to evaluate such as:

- The device is not running
- The device target temperature is set to a normal range
- The device target temperature is set to an abnormal range

We use the pre-canned restorable states to simplify data generation to not need
to consider every possibibility. This is implemented effectively as if setting
these attributes in the config file.
