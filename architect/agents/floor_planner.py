"""Floor Planner agent -- structured JSON output, one floor at a time.

Receives the architect spec and current floor index, then produces exact 2-D
geometry (walls, slabs, ceilings, zones, doors, windows, roofs) for that floor.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from architect.state import BuildState

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "floor_planner.md"


def _strip_markdown_fences(text: str) -> str:
    """Remove optional ```json ... ``` fences from an LLM response."""
    text = text.strip()
    text = re.sub(r"^```(?:json|jsonc)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def floor_planner_agent(state: BuildState, model: BaseChatModel) -> dict:
    """Plan the geometry for a single floor.

    Reads the current floor's room spec from the architect specification,
    sends it to the LLM with contextual information (footprint, wall height,
    roof type, top-floor flag), and parses the JSON response.

    Returns ``{"floor_plans": updated_plans}`` on success, or
    ``{"errors": [...]}`` on failure after 3 attempts.
    """
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    spec = state["architect_spec"]
    floor_idx = state["current_floor_index"]
    total_floors = state["total_floors"]
    levels = spec.get("levels", [])

    # Current floor's room specification
    floor_spec = levels[floor_idx] if floor_idx < len(levels) else {}
    is_top_floor = floor_idx == total_floors - 1

    user_content = json.dumps(
        {
            "level_index": floor_idx,
            "floor_spec": floor_spec,
            "buildingFootprint": spec.get("buildingFootprint", [10, 10]),
            "exteriorWallHeight": spec.get("exteriorWallHeight", 3.0),
            "roofType": spec.get("roofType", "flat"),
            "isTopFloor": is_top_floor,
        },
        indent=2,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    errors: list[str] = []

    for attempt in range(1, 4):
        response = model.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
        cleaned = _strip_markdown_fences(raw)

        try:
            floor_plan = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            errors.append(f"Attempt {attempt}: JSON parse error -- {exc}")
            continue

        updated_plans = list(state.get("floor_plans") or [])
        updated_plans.append(floor_plan)
        return {"floor_plans": updated_plans}

    return {"errors": errors}
