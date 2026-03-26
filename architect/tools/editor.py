"""LangChain @tool wrappers around the EditorClient.

Each tool is a thin synchronous wrapper that delegates to the async
EditorClient via ``_run()``.  A module-level ``set_client()`` function
must be called once before any tool is invoked.
"""

from __future__ import annotations

import asyncio
import math
from typing import Any

from langchain_core.tools import tool

from architect.client import EditorClient

# ---------------------------------------------------------------------------
# Module-level client singleton
# ---------------------------------------------------------------------------

_client: EditorClient | None = None


def set_client(client: EditorClient) -> None:
    """Set the global EditorClient that all tools will use."""
    global _client
    _client = client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro: Any) -> Any:
    """Run an async coroutine from a synchronous context."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()


def _wall_local_x(
    wall_start: list[float],
    wall_end: list[float],
    position_along_wall: float,
) -> float:
    """Door/window position[0] is distance from wall START (not center).
    The editor's wall-local coordinate system uses start-relative x."""
    return position_along_wall


def _extract(result: dict) -> dict:
    """Extract the data payload from an EditorClient response."""
    return result.get("data", result)


# ---------------------------------------------------------------------------
# Tools — state queries
# ---------------------------------------------------------------------------


@tool
def read_state() -> dict:
    """Read the full editor state."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _extract(_run(_client.read_state()))


@tool
def read_nodes(node_type: str | None = None) -> dict:
    """Read nodes from the editor, optionally filtered by node_type."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _extract(_run(_client.read_nodes(node_type=node_type)))


# ---------------------------------------------------------------------------
# Tools — creation helpers
# NOTE: We do NOT generate IDs here. The browser-side command handler
# passes nodes through Zod .parse() which auto-generates proper IDs
# in the {type}_{nanoid} format.
# ---------------------------------------------------------------------------


@tool
def create_wall(
    level_id: str,
    start: list[float],
    end: list[float],
    thickness: float = 0.1,
    height: float = 2.5,
    front_side: str = "unknown",
    back_side: str = "unknown",
) -> dict:
    """Create a wall on the given level. start/end are [x, z] coordinates in metres."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "type": "wall",
        "start": start,
        "end": end,
        "thickness": thickness,
        "height": height,
        "frontSide": front_side,
        "backSide": back_side,
    }
    return _extract(_run(_client.create_node(node, parent_id=level_id)))


@tool
def create_slab(
    level_id: str,
    polygon: list[list[float]],
    elevation: float = 0.05,
) -> dict:
    """Create a floor slab. polygon is list of [x, z] points in metres."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "type": "slab",
        "polygon": polygon,
        "elevation": elevation,
    }
    return _extract(_run(_client.create_node(node, parent_id=level_id)))


@tool
def create_ceiling(
    level_id: str,
    polygon: list[list[float]],
    height: float = 2.5,
) -> dict:
    """Create a ceiling. polygon is list of [x, z] points in metres."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "type": "ceiling",
        "polygon": polygon,
        "height": height,
    }
    return _extract(_run(_client.create_node(node, parent_id=level_id)))


@tool
def create_zone(
    level_id: str,
    name: str,
    polygon: list[list[float]],
    color: str = "#3b82f6",
) -> dict:
    """Create a named zone (room). polygon is list of [x, z] points in metres."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "type": "zone",
        "name": name,
        "polygon": polygon,
        "color": color,
    }
    return _extract(_run(_client.create_node(node, parent_id=level_id)))


@tool
def create_door(
    wall_id: str,
    wall_start: list[float],
    wall_end: list[float],
    position_along_wall: float,
    width: float = 0.9,
    height: float = 2.1,
    side: str = "front",
    hinges_side: str = "left",
    swing_direction: str = "inward",
) -> dict:
    """Create a door on a wall. position_along_wall is distance in metres from wall START.
    IMPORTANT: parentId MUST be the wall_id for CSG cutouts to work."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    x_local = _wall_local_x(wall_start, wall_end, position_along_wall)
    node = {
        "type": "door",
        "position": [x_local, height / 2, 0],
        "rotation": [0, 0, 0],
        "width": width,
        "height": height,
        "side": side,
        "hingesSide": hinges_side,
        "swingDirection": swing_direction,
        "wallId": wall_id,
    }
    return _extract(_run(_client.create_node(node, parent_id=wall_id)))


@tool
def create_window(
    wall_id: str,
    wall_start: list[float],
    wall_end: list[float],
    position_along_wall: float,
    width: float = 1.5,
    height: float = 1.5,
    side: str = "front",
    sill_height: float = 0.9,
) -> dict:
    """Create a window on a wall. position_along_wall is distance in metres from wall START.
    IMPORTANT: parentId MUST be the wall_id for CSG cutouts to work."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    x_local = _wall_local_x(wall_start, wall_end, position_along_wall)
    node = {
        "type": "window",
        "position": [x_local, sill_height + height / 2, 0],
        "rotation": [0, 0, 0],
        "width": width,
        "height": height,
        "side": side,
        "wallId": wall_id,
    }
    return _extract(_run(_client.create_node(node, parent_id=wall_id)))


@tool
def create_roof(
    level_id: str,
    center_x: float,
    center_z: float,
    width: float,
    depth: float,
    roof_type: str = "gable",
    roof_height: float = 2.5,
    wall_height: float = 0.5,
    rotation: float = 0,
) -> dict:
    """Create a roof on a level. RoofNode position = world center of footprint.
    For walls at (0,0)-(12,8), use center_x=6, center_z=4, width=12, depth=8.
    Only works on simple rectangular volumes — never on L/T/U shapes."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"

    # RoofNode at the world center of the footprint
    roof_node = {
        "type": "roof",
        "position": [center_x, 0, center_z],
        "rotation": rotation,
    }
    roof_result = _extract(_run(_client.create_node(roof_node, parent_id=level_id)))
    roof_id = roof_result.get("nodeId")

    # RoofSegmentNode at [0,0,0] local (centered in parent)
    segment_node = {
        "type": "roof-segment",
        "roofType": roof_type,
        "position": [0, 0, 0],
        "rotation": 0,
        "width": width,
        "depth": depth,
        "wallHeight": wall_height,
        "roofHeight": roof_height,
        "wallThickness": 0.1,
        "deckThickness": 0.1,
        "overhang": 0.3,
        "shingleThickness": 0.05,
    }
    seg_result = _extract(_run(_client.create_node(segment_node, parent_id=roof_id)))

    return {"roofId": roof_id, "segmentId": seg_result.get("nodeId")}


@tool
def create_level(building_id: str, level_number: int) -> dict:
    """Create a new level (storey) under a building node."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "type": "level",
        "level": level_number,
    }
    return _extract(_run(_client.create_node(node, parent_id=building_id)))


@tool
def create_item(
    parent_id: str,
    asset_id: str,
    asset_name: str,
    asset_src: str,
    asset_category: str,
    dimensions: list[float],
    position: list[float],
    rotation: list[float] | None = None,
    wall_id: str | None = None,
    wall_t: float | None = None,
    side: str | None = None,
) -> dict:
    """Place a furniture / fixture item. parent_id is the level (floor items) or wall (wall-mounted)."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"

    asset = {
        "id": asset_id,
        "category": asset_category,
        "name": asset_name,
        "thumbnail": "",
        "src": asset_src,
        "dimensions": dimensions,
        "offset": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [1, 1, 1],
    }

    node: dict[str, Any] = {
        "type": "item",
        "asset": asset,
        "position": position,
        "rotation": rotation or [0, 0, 0],
        "scale": [1, 1, 1],
    }
    if wall_id is not None:
        node["wallId"] = wall_id
    if wall_t is not None:
        node["wallT"] = wall_t
    if side is not None:
        node["side"] = side

    return _extract(_run(_client.create_node(node, parent_id=parent_id)))


# ---------------------------------------------------------------------------
# Tools — assets
# ---------------------------------------------------------------------------


@tool
def read_assets(category: str | None = None) -> list:
    """Read the available asset catalog, optionally filtered by category."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    result = _run(_client.read_assets(category=category))
    # Client returns {"id": ..., "ok": true, "data": [...]}
    if isinstance(result, dict):
        return result.get("data", result)
    return result


# ---------------------------------------------------------------------------
# Tools — editor actions
# ---------------------------------------------------------------------------


@tool
def select_level(level_id: str) -> dict:
    """Select a level in the editor."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _run(_client.set_selection(levelId=level_id))


@tool
def undo() -> dict:
    """Undo the last editor operation."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _run(_client.undo())


@tool
def clear_scene() -> dict:
    """Clear the entire editor scene."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _run(_client.clear())
