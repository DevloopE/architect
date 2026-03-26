"""Furnisher agent -- ReAct agent that places furniture in each room.

Uses ``create_react_agent`` from ``langgraph.prebuilt`` with access to
``read_state``, ``read_assets``, and ``create_item`` tools.
"""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.language_models import BaseChatModel

from architect.state import BuildState
from architect.tools.editor import create_item, read_assets, read_state

try:
    from langgraph.prebuilt import create_react_agent
except ImportError:  # pragma: no cover
    create_react_agent = None  # type: ignore[assignment]

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "furnisher.md"

FURNISHER_TOOLS = [read_state, read_assets, create_item]


def furnisher_agent(state: BuildState, model: BaseChatModel) -> dict:
    """Furnish all rooms in the built building using a ReAct agent.

    The agent reads the building state and asset catalog, then places
    appropriate furniture into each zone.  Placed item IDs are extracted
    from the agent's tool-call history and appended to ``built_node_ids``.

    Returns ``{"built_node_ids": updated_list}``.
    """
    if create_react_agent is None:
        return {"errors": ["langgraph is not installed -- cannot run furnisher"]}

    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    level_ids = state.get("level_ids", [])
    level_ids_text = ", ".join(level_ids) if level_ids else "(unknown)"

    task_description = (
        f"Furnish all rooms in the building. "
        f"The building has the following level IDs: {level_ids_text}. "
        f"Read the state to discover zones, then place furniture accordingly."
    )

    agent = create_react_agent(model, FURNISHER_TOOLS, prompt=system_prompt)

    result = agent.invoke({"messages": [("human", task_description)]})

    # ------------------------------------------------------------------
    # Extract placed item IDs from the agent's message history
    # ------------------------------------------------------------------
    built_node_ids = list(state.get("built_node_ids") or [])

    messages = result.get("messages", [])
    for msg in messages:
        # Tool messages contain the return value of create_item calls
        if hasattr(msg, "name") and msg.name == "create_item":
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            # Try to extract node IDs from the tool response
            # Pattern: "id": "..." or "nodeId": "..."
            for match in re.finditer(r'"(?:id|nodeId)"\s*:\s*"([^"]+)"', content):
                node_id = match.group(1)
                if node_id not in built_node_ids:
                    built_node_ids.append(node_id)

    return {"built_node_ids": built_node_ids}
