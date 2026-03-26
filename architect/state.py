from __future__ import annotations
from typing import TypedDict


class BuildState(TypedDict, total=False):
    prompt: str
    model_name: str
    editor_url: str
    ws_url: str
    architect_spec: dict | None
    current_floor_index: int
    total_floors: int
    floor_plans: list[dict]
    built_node_ids: list[str]
    building_id: str | None
    level_ids: list[str]
    wall_id_map: dict[int, list[str]]
    errors: list[str]
