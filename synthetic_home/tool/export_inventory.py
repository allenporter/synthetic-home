"""Export an inventory from a Home Assistant instance.

You can create a synthetic home inventory copied from an existing home assistant
instance. You need to create an access token and export an inventory like this:

```bash
$ HASS_URL="http://home-assistant.home-assistant:8123"
$ API_TOKEN="XXXXXXXXXXX"
$ synthetic-home --debug export_inventory "${HASS_URL}" "${API_TOKEN}" > inventory.yaml
```
"""

import argparse
import logging
import slugify
from typing import Any

import aiohttp

from synthetic_home import inventory, common

_LOGGER = logging.getLogger(__name__)

AREA_REGISTRY_LIST = "config/area_registry/list"
DEVICE_REGISTRY_LIST = "config/device_registry/list"
ENTITY_REGISTRY_LIST = "config/entity_registry/list"
GET_STATES = "get_states"
GET_CONFIG = "get_config"

DOMAINS = {
    "binary_sensor",
    # TODO: Support calendar
    # "calendar",
    "camera",
    "climate",
    "cover",
    "fan",
    # TODO: Support event
    # "event",
    "light",
    "lock",
    "media_player",
    # TODO: Support number, person, remote, select
    # "number",
    # "person",
    # "remote",
    # "select",
    "sensor",
    "switch",
    "todo",
    "vacuum",
    "weather",
    # TODO: Support zone
    # "zone",
}

STRIP_ATTRIBUTES = {
    "friendly_name",
    "icon",
}


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "homeassistant_url",
        type=str,
        help="Specifies url to the home assistant instance.",
    )
    args.add_argument(
        "auth_token",
        type=str,
        help="Specifies home assistant API token.",
    )


class Counter:

    def __init__(self) -> None:
        """Counter."""
        self._value = 0

    def increment(self) -> int:
        """Return next value."""
        self._value += 1
        return self._value


next_id = Counter()


async def auth_login(ws: aiohttp.ClientWebSocketResponse, auth_token: str) -> None:
    """Login to the websocket."""
    auth_resp = await ws.receive_json()
    assert auth_resp["type"] == "auth_required"

    await ws.send_json({"type": "auth", "access_token": auth_token})

    auth_ok = await ws.receive_json()
    assert auth_ok["type"] == "auth_ok"


async def fetch_config(ws: aiohttp.ClientWebSocketResponse) -> dict[str, Any]:
    """Fetch areas from websocket."""
    await ws.send_json({"id": next_id.increment(), "type": GET_CONFIG})
    data = await ws.receive_json()
    _LOGGER.info(data["result"])
    assert data["result"]
    return data["result"]  # type: ignore[no-any-return]


async def fetch_areas(ws: aiohttp.ClientWebSocketResponse) -> dict[str, inventory.Area]:
    """Fetch areas from websocket."""
    await ws.send_json({"id": next_id.increment(), "type": AREA_REGISTRY_LIST})
    data = await ws.receive_json()
    areas = {
        area["area_id"]: inventory.Area(
            id=slugify.slugify(area["name"], separator="_"),
            name=area["name"],
            floor=area["floor_id"],
        )
        for area in data["result"]
    }
    return areas


async def fetch_devices(
    ws: aiohttp.ClientWebSocketResponse, areas: dict[str, inventory.Area]
) -> dict[str, inventory.Device]:
    """Fetch areas from websocket."""

    await ws.send_json({"id": next_id.increment(), "type": DEVICE_REGISTRY_LIST})
    data = await ws.receive_json()

    devices = {}
    for device in data["result"]:
        if device.get("disabled_by") is not None:
            continue
        inv_device = inventory.Device(
            name=device["name"],
            id=slugify.slugify(device["name"], separator="_"),
        )
        if any(device.get(n) for n in ("model", "manufacturer", "sw_version")):
            device_info = common.DeviceInfo()
            if model := device.get("model"):
                device_info.model = model
            if manufacturer := device.get("manufacturer"):
                device_info.manufacturer = manufacturer
            if sw_version := device.get("sw_version"):
                device_info.model = sw_version
            inv_device.info = device_info
        if area_id := device.get("area_id"):
            inv_device.area = areas[area_id].id
        devices[device["id"]] = inv_device
    return devices


async def fetch_entities(
    ws: aiohttp.ClientWebSocketResponse,
    areas: dict[str, inventory.Area],
    devices: dict[str, inventory.Device],
) -> dict[str, inventory.Entity]:
    """Fetch devices from websocket."""
    await ws.send_json({"id": next_id.increment(), "type": ENTITY_REGISTRY_LIST})
    data = await ws.receive_json()

    entities = {}
    for entity in data["result"]:
        if entity.get("disabled_by") is not None:
            continue
        if entity.get("hidden_by") is not None:
            continue
        if entity.get("entity_category") in ("diagnostic", "config"):
            continue
        entity_id = entity["entity_id"]
        domain = entity_id.split(".", maxsplit=1)[0]
        if domain not in DOMAINS:
            _LOGGER.debug(
                "Skipping entity with unsupported domain %s (%s)",
                entity_id,
                domain,
            )
            continue
        inv_entity = inventory.Entity(
            name=entity["name"],
            id=entity_id,
        )
        if area_id := entity.get("area_id"):
            inv_entity.area = areas[area_id].id
        if device_id := entity.get("device_id"):
            inv_entity.device = devices[device_id].id
        entities[entity_id] = inv_entity
    return entities


async def build_states(
    ws: aiohttp.ClientWebSocketResponse,
    entities: dict[str, inventory.Entity],
    unit_system: dict[str, str],
) -> list[inventory.Entity]:
    """Fetch states from websocket and update inventory."""

    await ws.send_json({"id": next_id.increment(), "type": GET_STATES})
    data = await ws.receive_json()

    temperature_unit = unit_system["temperature"]
    results = []
    for state in data["result"]:
        entity_id = state["entity_id"]
        if (inv_entity := entities.get(entity_id)) is None:
            continue
        entity_state = state["state"]
        if entity_state in ("unavailable", "unknown"):
            continue
        inv_entity.state = entity_state
        if (attributes := state.get("attributes")) is not None:
            if friendly_name := attributes.get("friendly_name"):
                inv_entity.name = friendly_name.strip()
            inv_attributes = {
                k: v
                for k, v in attributes.items()
                if (v is not None) and (k not in STRIP_ATTRIBUTES)
            }

            if entity_id.startswith("climate."):
                inv_attributes["unit_of_measurement"] = temperature_unit
            if inv_attributes:
                inv_entity.attributes = inv_attributes
        results.append(inv_entity)
    return results


async def run(args: argparse.Namespace) -> int:
    url = args.homeassistant_url
    auth_token = args.auth_token

    async with aiohttp.ClientSession() as session:
        area_url = f"{url}/api/websocket"
        _LOGGER.info("Fetching areas from %s", url)
        async with session.ws_connect(area_url) as ws:
            await auth_login(ws, auth_token)

            config = await fetch_config(ws)
            unit_system = config["unit_system"]
            areas = await fetch_areas(ws)
            devices = await fetch_devices(ws, areas)
            entities = await fetch_entities(ws, areas, devices)

            required_device_ids = set({entity.device for entity in entities.values()})

            # Only include required devices for entities
            inv = inventory.Inventory()

            # Fetch state for all relevant entities
            inv.entities = await build_states(ws, entities, unit_system)
            inv.areas = list(areas.values())
            inv.devices = [
                device
                for device in devices.values()
                if device.id in required_device_ids
            ]

            print(inv.yaml())

    return 0
