"""Test for inventory."""

import pathlib

import pytest
from syrupy import SnapshotAssertion

from synthetic_home import inventory


INVENTORY = """
---
areas:
- name: Backyard
  id: backyard
  floor: Ground
- name: Frontyard
  id: frontyard
  floor: Ground
- name: Living Room
  id: living_room
  floor: Ground
- name: Loft
  id: loft
  floor: Upstairs
- name: Basement
  id: basement
"""

def test_floors() -> None:
    """Test floor logic"""
    inv = inventory.decode_inventory(INVENTORY)
    assert inv.floors == set({"Ground", "Upstairs"})
    assert len(inv.areas) == 5
