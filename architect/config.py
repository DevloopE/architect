"""Model registry and default configuration constants."""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_WS_URL = "ws://localhost:3100"
DEFAULT_EDITOR_URL = "http://localhost:3002"


def get_model(model_name: str) -> ChatAnthropic | ChatOpenAI:
    """Return a LangChain chat model for the given model name.

    Args:
        model_name: A model identifier string.
            - Names starting with ``claude-`` return a ``ChatAnthropic`` instance.
            - Names starting with ``gpt-`` or ``o`` return a ``ChatOpenAI`` instance.

    Raises:
        ValueError: If *model_name* does not match any known prefix.
    """
    if model_name.startswith("claude-"):
        return ChatAnthropic(model=model_name)
    if model_name.startswith("gpt-") or model_name.startswith("o"):
        return ChatOpenAI(model=model_name)
    raise ValueError(
        f"Unknown model: {model_name!r}. "
        "Expected a name starting with 'claude-', 'gpt-', or 'o'."
    )
