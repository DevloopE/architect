"""Architect agent -- pure reasoning, no tools.

Takes a natural-language building description and produces a structured JSON
specification consumed by downstream agents.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from architect.state import BuildState

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "architect.md"


def _strip_markdown_fences(text: str) -> str:
    """Remove optional ```json ... ``` fences from an LLM response."""
    text = text.strip()
    text = re.sub(r"^```(?:json|jsonc)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def architect_agent(state: BuildState, model: BaseChatModel) -> dict:
    """Generate a building specification from a natural-language prompt.

    Sends the architect system prompt plus the user's description to the LLM
    and parses the response as JSON.  Retries up to 3 times on invalid JSON.

    Returns a dict with ``architect_spec``, ``total_floors``, and supporting
    state keys, or ``{"errors": [...]}`` on failure.
    """
    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["prompt"]),
    ]

    errors: list[str] = []

    for attempt in range(1, 4):
        response = model.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
        cleaned = _strip_markdown_fences(raw)

        try:
            spec = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            errors.append(f"Attempt {attempt}: JSON parse error -- {exc}")
            continue

        return {
            "architect_spec": spec,
            "total_floors": spec.get("floors", 1),
            "current_floor_index": 0,
            "floor_plans": [],
            "built_node_ids": [],
            "level_ids": [],
            "wall_id_map": {},
            "errors": [],
        }

    return {"errors": errors}
