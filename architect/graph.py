"""LangGraph state machine for the Architect pipeline.

Orchestrates four agents in sequence:
    Architect -> (Floor Planner -> Builder) x N floors -> Furnisher
"""

from __future__ import annotations

from functools import partial

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph

from architect.agents.architect import architect_agent
from architect.agents.builder import builder_agent
from architect.agents.floor_planner import floor_planner_agent
from architect.agents.furnisher import furnisher_agent
from architect.state import BuildState


# ------------------------------------------------------------------
# Conditional-edge helpers
# ------------------------------------------------------------------

def check_architect_success(state: BuildState) -> str:
    """Return 'failed' if the architect produced errors, else 'success'."""
    if state.get("errors"):
        return "failed"
    return "success"


def check_floors_remaining(state: BuildState) -> str:
    """Return 'done' if there are errors or all floors are built, else 'more_floors'."""
    if state.get("errors"):
        return "done"
    if state.get("current_floor_index", 0) >= state.get("total_floors", 0):
        return "done"
    return "more_floors"


# ------------------------------------------------------------------
# Graph construction
# ------------------------------------------------------------------

def build_graph(model: BaseChatModel) -> StateGraph:
    """Build (but do not compile) the architect state-machine graph.

    Parameters
    ----------
    model:
        The chat model injected into every agent that needs one.
        The builder agent is deterministic and receives no model.
    """
    graph = StateGraph(BuildState)

    # Wrap each agent so it receives the shared model.
    # Builder is deterministic -- it ignores the model parameter.
    graph.add_node("architect", partial(architect_agent, model=model))
    graph.add_node("floor_planner", partial(floor_planner_agent, model=model))
    graph.add_node("builder", builder_agent)
    graph.add_node("furnisher", partial(furnisher_agent, model=model))

    # Entry point
    graph.set_entry_point("architect")

    # Architect -> floor_planner on success, END on failure
    graph.add_conditional_edges(
        "architect",
        check_architect_success,
        {"success": "floor_planner", "failed": END},
    )

    # floor_planner -> builder (always)
    graph.add_edge("floor_planner", "builder")

    # builder -> floor_planner if more floors, furnisher if done
    graph.add_conditional_edges(
        "builder",
        check_floors_remaining,
        {"more_floors": "floor_planner", "done": "furnisher"},
    )

    # furnisher -> END
    graph.add_edge("furnisher", END)

    return graph


def compile_graph(model: BaseChatModel):
    """Build and compile the architect graph, ready for invocation."""
    return build_graph(model).compile()
