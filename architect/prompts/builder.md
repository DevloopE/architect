The builder agent is DETERMINISTIC — it does not use LLM reasoning.
It executes the floor plan step-by-step using Python code, not a ReAct agent.
Wall IDs are tracked in an ordered Python list for reliable door/window placement.
See architect/agents/builder.py for the implementation.
