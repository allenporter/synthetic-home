"""Test for inventory."""

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


TODO_LIST_INVENTORY = """
---
devices:
- name: Tasks
  id: tasks
entities:
- name: Tasks
  id: todo.tasks
  device: tasks
  state: '2'
  attributes:
    todo_items:
    - summary: Homework
    - summary: Call mom
"""


def test_todo_list_entity_attributes() -> None:
    """Test loading a todo list entity and validating structured attributes."""
    inv = inventory.decode_inventory(TODO_LIST_INVENTORY)
    assert len(inv.entities) == 1
    entity = inv.entities[0]
    assert entity.name == "Tasks"
    assert entity.id == "todo.tasks"
    assert entity.attributes == {
        "todo_items": [
            {
                "summary": "Homework",
            },
            {
                "summary": "Call mom",
            },
        ]
    }
