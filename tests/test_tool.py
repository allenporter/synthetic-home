"""Tests for the sythethic-home `create_inventory` command."""

import shlex
import subprocess
import asyncio
import logging
import pathlib

import pytest

from syrupy.assertion import SnapshotAssertion


_LOGGER = logging.getLogger(__name__)

BIN = "synthetic-home"

TEST_HOMES = pathlib.Path("tests/homes")


async def run(cmd: list[str], stdin: bytes | None = None) -> bytes:
    """Run the command, returning stdout."""
    cmd_string = " ".join([shlex.quote(arg) for arg in cmd])
    _LOGGER.debug("Running command: %s", cmd_string)
    proc = await asyncio.create_subprocess_shell(
        cmd_string,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = await proc.communicate(stdin)
    if proc.returncode:
        errors = [f"Command '{cmd_string}' failed with return code {proc.returncode}"]
        if out:
            errors.append(out.decode("utf-8"))
        if err:
            errors.append(err.decode("utf-8"))
        _LOGGER.debug("\n".join(errors))
        raise ValueError("\n".join(errors))
    return out


@pytest.mark.parametrize(
    ("home_filename"),
    list(TEST_HOMES.glob("*.yaml")),
    ids=[str(filename) for filename in TEST_HOMES.glob("*.yaml")],
)
async def test_build(home_filename: pathlib.Path, snapshot: SnapshotAssertion) -> None:
    """Test build commands."""
    result = await run([BIN, "create_inventory", str(home_filename)])
    str_result = result.decode("utf-8")
    assert str_result == snapshot
