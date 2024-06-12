"""Script to export an inventory from a Home Assistant instance."""

import argparse
import logging
import slugify

import aiohttp

from synthetic_home import inventory, common

_LOGGER = logging.getLogger(__name__)

AREA_REGISTRY_LIST = "config/area_registry/list"
DEVICE_REGISTRY_LIST = "config/device_registry/list"
ENTITY_REGISTRY_LIST = "config/entity_registry/list"
GET_STATES = "get_states"

DOMAINS = {
    "binary_sensor",
    # TODO: Support calendar
    # "calendar",
    "camera",
    "climate",
    "cover",
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


async def fetch_areas(ws: aiohttp.ClientWebSocketResponse) -> dict[str, inventory.Area]:
    """Fetch areas from websocket."""
    await ws.send_json({"id": 1, "type": AREA_REGISTRY_LIST})
    data = await ws.receive_json()
    assert data["id"] == 1
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

    await ws.send_json({"id": 2, "type": DEVICE_REGISTRY_LIST})
    data = await ws.receive_json()
    assert data["id"] == 2

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
    await ws.send_json({"id": 3, "type": ENTITY_REGISTRY_LIST})
    data = await ws.receive_json()
    assert data["id"] == 3

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
    ws: aiohttp.ClientWebSocketResponse, entities: dict[str, inventory.Entity]
) -> None:
    """Fetch states from websocket and update inventory."""

    await ws.send_json({"id": 4, "type": GET_STATES})
    data = await ws.receive_json()
    assert data["id"] == 4

    for state in data["result"]:
        entity_id = state["entity_id"]
        if (inv_entity := entities.get(entity_id)) is None:
            continue
        inv_entity.state = state["state"]
        if (attributes := state.get("attributes")) is not None:
            if friendly_name := attributes.get("friendly_name"):
                inv_entity.name = friendly_name.strip()
            inv_attributes = {
                k: v
                for k, v in attributes.items()
                if (v is not None) and (k not in STRIP_ATTRIBUTES)
            }
            if inv_attributes:
                inv_entity.attributes = inv_attributes


async def run(args: argparse.Namespace) -> int:
    url = args.homeassistant_url
    auth_token = args.auth_token

    # if url.startswith("https://"):
    #     url = "wss://" + url[6:]
    # elif url.startswith("http://"):
    #     url = "ws://" + url[5:]
    # else:
    #     raise ValueError("Unable to parse url did not start with 'http://' or 'https://': {url}")
    # print(url)

    async with aiohttp.ClientSession() as session:
        area_url = f"{url}/api/websocket"
        _LOGGER.info("Fetching areas from %s", url)
        async with session.ws_connect(area_url) as ws:
            auth_resp = await ws.receive_json()
            assert auth_resp["type"] == "auth_required"

            await ws.send_json({"type": "auth", "access_token": auth_token})

            auth_ok = await ws.receive_json()
            assert auth_ok["type"] == "auth_ok"

            areas = await fetch_areas(ws)
            devices = await fetch_devices(ws, areas)
            entities = await fetch_entities(ws, areas, devices)

            required_device_ids = set({entity.device for entity in entities.values()})

            # Fetch state for all relevant entities
            await build_states(ws, entities)

            # Only include required devices for entities
            inv = inventory.Inventory()
            inv.areas = list(areas.values())
            inv.devices = [
                device
                for device in devices.values()
                if device.id in required_device_ids
            ]
            inv.entities = list(entities.values())

            print(inv.yaml())

    # home = synthetic_home.load_synthetic_home(pathlib.Path(args.config_file))
    # inventory = synthetic_home.build_inventory(home)
    # print(inventory.yaml())
    return 0
