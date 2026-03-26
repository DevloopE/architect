"""LangChain @tool wrappers around the EditorClient.

Each tool is a thin synchronous wrapper that delegates to the async
EditorClient via ``_run()``.  A module-level ``set_client()`` function
must be called once before any tool is invoked.
"""

from __future__ import annotations

import asyncio
import math
from typing import Any
from uuid import uuid4

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
        loop = asyncio.get_running_loop()
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
    """Convert a distance-from-start to a wall-local centred x coordinate.

    The wall-local origin sits at the midpoint of the wall, so:
        ``local_x = position_along_wall - (wall_length / 2)``
    """
    dx = wall_end[0] - wall_start[0]
    dz = wall_end[1] - wall_start[1]
    wall_length = math.sqrt(dx * dx + dz * dz)
    return position_along_wall - (wall_length / 2)


# ---------------------------------------------------------------------------
# Tools — state queries
# ---------------------------------------------------------------------------


@tool
def read_state() -> dict:
    """Read the full editor state."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _run(_client.read_state())


@tool
def read_nodes(node_type: str | None = None) -> dict:
    """Read nodes from the editor, optionally filtered by node_type."""
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _run(_client.read_nodes(node_type=node_type))


# ---------------------------------------------------------------------------
# Tools — creation helpers
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
    """Create a wall on the given level.

    Args:
        level_id: Parent level node ID.
        start: Wall start point [x, z].
        end: Wall end point [x, z].
        thickness: Wall thickness in metres (default 0.1).
        height: Wall height in metres (default 2.5).
        front_side: Label for the front side of the wall.
        back_side: Label for the back side of the wall.
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "id": uuid4().hex[:12],
        "type": "WallNode",
        "start": start,
        "end": end,
        "thickness": thickness,
        "height": height,
        "frontSide": front_side,
        "backSide": back_side,
    }
    return _run(_client.create_node(node, parent_id=level_id))


@tool
def create_slab(
    level_id: str,
    polygon: list[list[float]],
    elevation: float = 0.05,
) -> dict:
    """Create a floor slab on the given level.

    Args:
        level_id: Parent level node ID.
        polygon: List of [x, z] vertices forming the slab outline.
        elevation: Top-surface elevation in metres (default 0.05).
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "id": uuid4().hex[:12],
        "type": "SlabNode",
        "polygon": polygon,
        "elevation": elevation,
    }
    return _run(_client.create_node(node, parent_id=level_id))


@tool
def create_ceiling(
    level_id: str,
    polygon: list[list[float]],
    height: float = 2.5,
) -> dict:
    """Create a ceiling on the given level.

    Args:
        level_id: Parent level node ID.
        polygon: List of [x, z] vertices forming the ceiling outline.
        height: Ceiling height in metres (default 2.5).
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "id": uuid4().hex[:12],
        "type": "CeilingNode",
        "polygon": polygon,
        "height": height,
    }
    return _run(_client.create_node(node, parent_id=level_id))


@tool
def create_zone(
    level_id: str,
    name: str,
    polygon: list[list[float]],
    color: str = "#3b82f6",
) -> dict:
    """Create a zone (room label) on the given level.

    Args:
        level_id: Parent level node ID.
        name: Human-readable room name / type.
        polygon: List of [x, z] vertices forming the zone boundary.
        color: Hex colour for the zone (default '#3b82f6').
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "id": uuid4().hex[:12],
        "type": "ZoneNode",
        "name": name,
        "polygon": polygon,
        "color": color,
    }
    return _run(_client.create_node(node, parent_id=level_id))


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
    """Create a door on a wall.

    Args:
        wall_id: ID of the parent wall (CRITICAL — used for CSG).
        wall_start: Wall start point [x, z].
        wall_end: Wall end point [x, z].
        position_along_wall: Distance in metres from wall start to door centre.
        width: Door width in metres (default 0.9).
        height: Door height in metres (default 2.1).
        side: Which side the door opens toward ('front' or 'back').
        hinges_side: Hinge placement ('left' or 'right').
        swing_direction: Swing direction ('inward' or 'outward').
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    x_local = _wall_local_x(wall_start, wall_end, position_along_wall)
    node = {
        "id": uuid4().hex[:12],
        "type": "DoorNode",
        "position": [x_local, height / 2, 0],
        "width": width,
        "height": height,
        "side": side,
        "hingesSide": hinges_side,
        "swingDirection": swing_direction,
        "wallId": wall_id,
    }
    return _run(_client.create_node(node, parent_id=wall_id))


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
    """Create a window on a wall.

    Args:
        wall_id: ID of the parent wall (CRITICAL — used for CSG).
        wall_start: Wall start point [x, z].
        wall_end: Wall end point [x, z].
        position_along_wall: Distance in metres from wall start to window centre.
        width: Window width in metres (default 1.5).
        height: Window height in metres (default 1.5).
        side: Which side the window faces ('front' or 'back').
        sill_height: Height of the window sill above floor (default 0.9).
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    x_local = _wall_local_x(wall_start, wall_end, position_along_wall)
    node = {
        "id": uuid4().hex[:12],
        "type": "WindowNode",
        "position": [x_local, sill_height + height / 2, 0],
        "width": width,
        "height": height,
        "side": side,
        "sillHeight": sill_height,
        "wallId": wall_id,
    }
    return _run(_client.create_node(node, parent_id=wall_id))


@tool
def create_roof(
    level_id: str,
    roof_type: str = "gable",
    width: float = 8,
    depth: float = 6,
    roof_height: float = 2.5,
    wall_height: float = 0.5,
) -> dict:
    """Create a roof on the given level (RoofNode + RoofSegmentNode).

    Args:
        level_id: Parent level node ID.
        roof_type: Roof style ('flat', 'gable', or 'hip').
        width: Roof span along X axis in metres.
        depth: Roof span along Z axis in metres.
        roof_height: Ridge height above the wall top in metres.
        wall_height: Short wall (knee wall) height in metres.
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"

    roof_id = uuid4().hex[:12]
    roof_node = {
        "id": roof_id,
        "type": "RoofNode",
        "roofType": roof_type,
        "width": width,
        "depth": depth,
        "roofHeight": roof_height,
        "wallHeight": wall_height,
    }
    result_roof = _run(_client.create_node(roof_node, parent_id=level_id))

    segment_id = uuid4().hex[:12]
    segment_node = {
        "id": segment_id,
        "type": "RoofSegmentNode",
        "width": width,
        "depth": depth,
        "roofHeight": roof_height,
        "wallHeight": wall_height,
    }
    _run(_client.create_node(segment_node, parent_id=roof_id))

    return {"roofId": roof_id, "segmentId": segment_id}


@tool
def create_level(building_id: str, level_number: int) -> dict:
    """Create a new level (storey) under a building node.

    Args:
        building_id: Parent building node ID.
        level_number: Zero-based index of the level.
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    node = {
        "id": uuid4().hex[:12],
        "type": "LevelNode",
        "levelNumber": level_number,
    }
    return _run(_client.create_node(node, parent_id=building_id))


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
    """Place a furniture / fixture item into the scene.

    Args:
        parent_id: Parent node ID (level for floor items, wall for wall-mounted).
        asset_id: Unique asset identifier from the catalog.
        asset_name: Human-readable asset name.
        asset_src: Source URL / path for the 3-D model.
        asset_category: Asset category string.
        dimensions: Bounding-box [width, height, depth] in metres.
        position: Placement position [x, y, z].
        rotation: Optional rotation [rx, ry, rz] in degrees.
        wall_id: Optional parent wall ID for wall-mounted items.
        wall_t: Optional parametric position along the wall (0-1).
        side: Optional wall side ('front' or 'back').
    """
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
        "id": uuid4().hex[:12],
        "type": "ItemNode",
        "asset": asset,
        "position": position,
    }
    if rotation is not None:
        node["rotation"] = rotation
    if wall_id is not None:
        node["wallId"] = wall_id
    if wall_t is not None:
        node["wallT"] = wall_t
    if side is not None:
        node["side"] = side

    return _run(_client.create_node(node, parent_id=parent_id))


# ---------------------------------------------------------------------------
# Tools — assets
# ---------------------------------------------------------------------------


@tool
def read_assets(category: str | None = None) -> list:
    """Read the available asset catalog, optionally filtered by category.

    Args:
        category: Optional category to filter assets by.
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    result = _run(_client.read_assets(category=category))
    # The client returns a dict with the response; extract the list if present.
    if isinstance(result, dict):
        return result.get("assets", result)
    return result


# ---------------------------------------------------------------------------
# Tools — editor actions
# ---------------------------------------------------------------------------


@tool
def select_level(level_id: str) -> dict:
    """Select a level in the editor.

    Args:
        level_id: ID of the level node to select.
    """
    assert _client is not None, "EditorClient not initialised — call set_client() first"
    return _run(_client.set_selection(level_id=level_id))


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
