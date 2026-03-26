"""Builder agent -- deterministic Python execution (no LLM).

Reads the floor plan produced by the Floor Planner and creates every geometric
element in the editor via tool calls.  Wall IDs are tracked in an ordered list
so that doors and windows can reference walls by index.
"""

from __future__ import annotations

from rich.console import Console

from architect.state import BuildState
from architect.tools.editor import (
    create_ceiling,
    create_door,
    create_level,
    create_roof,
    create_slab,
    create_wall,
    create_window,
    create_zone,
    read_state,
    select_level,
    undo,
)

console = Console()


def _safe_invoke(tool, args: dict, label: str, errors: list[str]) -> dict | None:
    """Invoke a tool, catching exceptions and logging errors."""
    try:
        result = tool.invoke(args)
        return result
    except Exception as exc:
        msg = f"{label}: {exc}"
        console.print(f"  [red]ERROR[/red] {msg}")
        errors.append(msg)
        return None


def builder_agent(state: BuildState, model=None) -> dict:
    """Execute a floor plan deterministically in the editor.

    This agent uses no LLM.  It iterates through slabs, walls, doors,
    windows, ceilings, zones, and roofs defined in the current floor plan
    and creates them via editor tool calls.

    Returns updated state keys including incremented ``current_floor_index``.
    """
    floor_idx = state.get("current_floor_index", 0)
    floor_plans = state.get("floor_plans", [])
    floor_plan = floor_plans[floor_idx]

    building_id = state.get("building_id")
    level_ids = list(state.get("level_ids") or [])
    built_node_ids = list(state.get("built_node_ids") or [])
    wall_id_map = dict(state.get("wall_id_map") or {})
    errors: list[str] = list(state.get("errors") or [])

    console.print(f"\n[bold cyan]Builder[/bold cyan] -- Floor {floor_idx}")

    # ------------------------------------------------------------------
    # 1. Discover or reuse building / level
    # ------------------------------------------------------------------
    if floor_idx == 0 or building_id is None:
        console.print("  Reading editor state ...")
        editor_state = _safe_invoke(read_state, {}, "read_state", errors)
        if editor_state is not None:
            # Nodes are a FLAT dict {id: node_obj} with lowercase type values
            nodes = editor_state.get("nodes", {})
            if isinstance(nodes, dict):
                for nid, node in nodes.items():
                    ntype = node.get("type", "")
                    if ntype == "building" and building_id is None:
                        building_id = nid
                    if ntype == "level" and nid not in level_ids:
                        level_ids.append(nid)

    # ------------------------------------------------------------------
    # 2. Create or reuse level
    # ------------------------------------------------------------------
    level_id: str | None = None

    if floor_idx == 0 and level_ids:
        # Reuse existing first level
        level_id = level_ids[0]
        console.print(f"  Reusing level [green]{level_id}[/green]")
    elif building_id:
        console.print(f"  Creating level {floor_idx} ...")
        result = _safe_invoke(
            create_level,
            {"building_id": building_id, "level_number": floor_idx},
            f"create_level({floor_idx})",
            errors,
        )
        if result is not None:
            new_level_id = result.get("id") or result.get("nodeId")
            if new_level_id:
                level_id = new_level_id
                if level_id not in level_ids:
                    level_ids.append(level_id)
    else:
        errors.append("No building_id available -- cannot create level")

    if level_id is None and level_ids:
        level_id = level_ids[-1]

    if level_id is None:
        errors.append("Could not determine level_id -- aborting floor build")
        return {
            "built_node_ids": built_node_ids,
            "building_id": building_id,
            "level_ids": level_ids,
            "wall_id_map": wall_id_map,
            "current_floor_index": floor_idx + 1,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # 3. Select the level
    # ------------------------------------------------------------------
    console.print(f"  Selecting level [green]{level_id}[/green]")
    _safe_invoke(select_level, {"level_id": level_id}, "select_level", errors)

    # ------------------------------------------------------------------
    # 4. Slabs
    # ------------------------------------------------------------------
    for slab in floor_plan.get("slabs", []):
        console.print(f"  Creating slab [yellow]{slab.get('id', '?')}[/yellow]")
        result = _safe_invoke(
            create_slab,
            {
                "level_id": level_id,
                "polygon": slab["polygon"],
                "elevation": slab.get("y", slab.get("elevation", 0.05)),
            },
            f"create_slab({slab.get('id', '?')})",
            errors,
        )
        if result:
            nid = result.get("id") or result.get("nodeId")
            if nid:
                built_node_ids.append(nid)

    # ------------------------------------------------------------------
    # 5. Walls (order matters -- doors/windows reference by index)
    # ------------------------------------------------------------------
    walls_data = floor_plan.get("walls", [])
    floor_wall_ids: list[str] = []

    # Build a lookup from wall plan-id to its list index
    wall_plan_id_to_index: dict[str, int] = {}
    for i, wall in enumerate(walls_data):
        if "id" in wall:
            wall_plan_id_to_index[wall["id"]] = i

    for wall in walls_data:
        console.print(f"  Creating wall [yellow]{wall.get('id', '?')}[/yellow]")
        result = _safe_invoke(
            create_wall,
            {
                "level_id": level_id,
                "start": wall["start"],
                "end": wall["end"],
                "thickness": wall.get("thickness", 0.1),
                "height": wall.get("height", 2.5),
            },
            f"create_wall({wall.get('id', '?')})",
            errors,
        )
        if result:
            nid = result.get("id") or result.get("nodeId")
            if nid:
                floor_wall_ids.append(nid)
                built_node_ids.append(nid)
            else:
                floor_wall_ids.append("")
        else:
            floor_wall_ids.append("")

    wall_id_map[floor_idx] = floor_wall_ids

    # ------------------------------------------------------------------
    # 6. Doors
    # ------------------------------------------------------------------
    for door in floor_plan.get("doors", []):
        # Resolve wall reference: by wall_index (int) or wall_id (plan id)
        wall_index = door.get("wall_index")
        if wall_index is None:
            plan_wall_id = door.get("wall_id", "")
            wall_index = wall_plan_id_to_index.get(plan_wall_id)

        if wall_index is None or wall_index >= len(floor_wall_ids):
            errors.append(f"Door {door.get('id', '?')}: invalid wall reference")
            continue

        actual_wall_id = floor_wall_ids[wall_index]
        if not actual_wall_id:
            errors.append(f"Door {door.get('id', '?')}: wall was not created")
            continue

        wall_spec = walls_data[wall_index]

        console.print(f"  Creating door [yellow]{door.get('id', '?')}[/yellow] on wall {wall_index}")
        result = _safe_invoke(
            create_door,
            {
                "wall_id": actual_wall_id,
                "wall_start": wall_spec["start"],
                "wall_end": wall_spec["end"],
                "position_along_wall": door["position_along_wall"],
                "width": door.get("width", 0.9),
                "height": door.get("height", 2.1),
            },
            f"create_door({door.get('id', '?')})",
            errors,
        )
        if result:
            nid = result.get("id") or result.get("nodeId")
            if nid:
                built_node_ids.append(nid)

    # ------------------------------------------------------------------
    # 7. Windows
    # ------------------------------------------------------------------
    for window in floor_plan.get("windows", []):
        wall_index = window.get("wall_index")
        if wall_index is None:
            plan_wall_id = window.get("wall_id", "")
            wall_index = wall_plan_id_to_index.get(plan_wall_id)

        if wall_index is None or wall_index >= len(floor_wall_ids):
            errors.append(f"Window {window.get('id', '?')}: invalid wall reference")
            continue

        actual_wall_id = floor_wall_ids[wall_index]
        if not actual_wall_id:
            errors.append(f"Window {window.get('id', '?')}: wall was not created")
            continue

        wall_spec = walls_data[wall_index]

        console.print(f"  Creating window [yellow]{window.get('id', '?')}[/yellow] on wall {wall_index}")
        result = _safe_invoke(
            create_window,
            {
                "wall_id": actual_wall_id,
                "wall_start": wall_spec["start"],
                "wall_end": wall_spec["end"],
                "position_along_wall": window["position_along_wall"],
                "width": window.get("width", 1.5),
                "height": window.get("height", 1.5),
                "sill_height": window.get("sill_height", 0.9),
            },
            f"create_window({window.get('id', '?')})",
            errors,
        )
        if result:
            nid = result.get("id") or result.get("nodeId")
            if nid:
                built_node_ids.append(nid)

    # ------------------------------------------------------------------
    # 8. Ceilings
    # ------------------------------------------------------------------
    for ceiling in floor_plan.get("ceilings", []):
        console.print(f"  Creating ceiling [yellow]{ceiling.get('id', '?')}[/yellow]")
        result = _safe_invoke(
            create_ceiling,
            {
                "level_id": level_id,
                "polygon": ceiling["polygon"],
                "height": ceiling.get("y", ceiling.get("height", 2.5)),
            },
            f"create_ceiling({ceiling.get('id', '?')})",
            errors,
        )
        if result:
            nid = result.get("id") or result.get("nodeId")
            if nid:
                built_node_ids.append(nid)

    # ------------------------------------------------------------------
    # 9. Zones
    # ------------------------------------------------------------------
    for zone in floor_plan.get("zones", []):
        console.print(f"  Creating zone [yellow]{zone.get('id', '?')}[/yellow] ({zone.get('room_type', '?')})")
        result = _safe_invoke(
            create_zone,
            {
                "level_id": level_id,
                "name": zone.get("room_type", zone.get("name", "room")),
                "polygon": zone["polygon"],
                "color": zone.get("color", "#3b82f6"),
            },
            f"create_zone({zone.get('id', '?')})",
            errors,
        )
        if result:
            nid = result.get("id") or result.get("nodeId")
            if nid:
                built_node_ids.append(nid)

    # ------------------------------------------------------------------
    # 10. Roof (top floor only)
    # ------------------------------------------------------------------
    total_floors = state.get("total_floors", 1)
    is_top_floor = floor_idx == total_floors - 1

    if is_top_floor:
        for roof in floor_plan.get("roofs", []):
            console.print(f"  Creating roof [yellow]{roof.get('id', '?')}[/yellow]")
            footprint = state.get("architect_spec", {}).get("buildingFootprint", [8, 6])
            result = _safe_invoke(
                create_roof,
                {
                    "level_id": level_id,
                    "roof_type": roof.get("type", "flat"),
                    "width": roof.get("width", footprint[0] if len(footprint) > 0 else 8),
                    "depth": roof.get("depth", footprint[1] if len(footprint) > 1 else 6),
                    "roof_height": roof.get("ridge_height", 2.5),
                    "wall_height": roof.get("wall_height", roof.get("eave_height", 0.5)),
                },
                f"create_roof({roof.get('id', '?')})",
                errors,
            )
            if result:
                roof_id = result.get("roofId")
                seg_id = result.get("segmentId")
                if roof_id:
                    built_node_ids.append(roof_id)
                if seg_id:
                    built_node_ids.append(seg_id)

    console.print(f"[bold cyan]Builder[/bold cyan] -- Floor {floor_idx} complete "
                   f"({len(errors)} errors)\n")

    return {
        "built_node_ids": built_node_ids,
        "building_id": building_id,
        "level_ids": level_ids,
        "wall_id_map": wall_id_map,
        "current_floor_index": floor_idx + 1,
        "errors": errors,
    }
