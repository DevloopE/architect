"""Unit tests for architect.client.EditorClient."""

from architect.client import EditorClient


def test_client_instantiation():
    client = EditorClient(ws_url="ws://localhost:3100")
    assert client.ws_url == "ws://localhost:3100"
    assert client._ws is None


def test_build_message():
    client = EditorClient(ws_url="ws://localhost:3100")
    msg = client._build_message("read_state", {})
    assert msg["type"] == "command"
    assert msg["payload"]["cmd"] == "read_state"
    assert "id" in msg["payload"]
