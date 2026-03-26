"""WebSocket client for the Pascal Editor relay server."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4

import websockets
from websockets.asyncio.client import ClientConnection


class EditorClient:
    """Async client that sends commands to the Pascal Editor via the WS relay.

    Parameters
    ----------
    ws_url:
        WebSocket URL of the relay server (default ``ws://localhost:3100``).
    """

    def __init__(self, ws_url: str = "ws://localhost:3100") -> None:
        self.ws_url = ws_url
        self._ws: ClientConnection | None = None
        self._listener_task: asyncio.Task[None] | None = None
        self._pending: dict[str, asyncio.Future[dict]] = {}
        self.browser_errors: list[str] = []

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the WebSocket connection and register as a Python client."""
        self._ws = await websockets.connect(self.ws_url)
        await self._ws.send(json.dumps({"type": "register", "role": "python"}))
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        """Background listener that resolves pending futures by message ID."""
        assert self._ws is not None
        try:
            async for raw in self._ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                # Browser error forwarding
                if msg.get("type") == "browser_error":
                    error_msg = msg.get("payload", "")
                    if len(self.browser_errors) > 500:
                        self.browser_errors.pop(0)
                    self.browser_errors.append(error_msg)
                    print(f"  [BROWSER ERROR] {error_msg[:200]}")
                    continue

                payload = msg.get("payload", msg)
                msg_id = payload.get("id")
                if msg_id and msg_id in self._pending:
                    self._pending[msg_id].set_result(payload)
        except websockets.ConnectionClosed:
            pass

    async def close(self) -> None:
        """Close the WebSocket and cancel the listener task."""
        if self._listener_task is not None:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------

    def _build_message(self, cmd: str, params: dict[str, Any]) -> dict[str, Any]:
        """Build a ``{"type": "command", "payload": {...}}`` envelope."""
        msg_id = uuid4().hex[:12]
        payload: dict[str, Any] = {"cmd": cmd, "id": msg_id, **params}
        return {"type": "command", "payload": payload}

    async def send(self, cmd: str, **params: Any) -> dict[str, Any]:
        """Send a command and wait up to 30 s for the correlated response.

        Raises
        ------
        RuntimeError
            If the WebSocket is not connected or the response indicates failure.
        """
        if self._ws is None:
            raise RuntimeError("WebSocket is not connected. Call connect() first.")

        msg = self._build_message(cmd, params)
        msg_id: str = msg["payload"]["id"]

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict] = loop.create_future()
        self._pending[msg_id] = future

        try:
            await self._ws.send(json.dumps(msg))
            result = await asyncio.wait_for(future, timeout=30)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Timeout waiting for response to {cmd!r} (id={msg_id})")
        finally:
            self._pending.pop(msg_id, None)

        if result.get("error"):
            raise RuntimeError(f"Command {cmd!r} failed: {result['error']}")

        return result

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    async def read_state(self) -> dict[str, Any]:
        """Read the full editor state."""
        return await self.send("read_state")

    async def read_nodes(self, node_type: str | None = None) -> dict[str, Any]:
        """Read nodes, optionally filtered by *node_type*."""
        params: dict[str, Any] = {}
        if node_type is not None:
            params["type"] = node_type
        return await self.send("read_nodes", **params)

    async def create_node(
        self, node: dict[str, Any], parent_id: str | None = None
    ) -> dict[str, Any]:
        """Create a single node, optionally under *parent_id*."""
        params: dict[str, Any] = {"node": node}
        if parent_id is not None:
            params["parentId"] = parent_id
        return await self.send("create_node", **params)

    async def create_nodes(self, ops: list[dict[str, Any]]) -> dict[str, Any]:
        """Create multiple nodes in one batch."""
        return await self.send("create_nodes", ops=ops)

    async def update_node(
        self, node_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a node by *node_id* with the given *data*."""
        return await self.send("update_node", nodeId=node_id, data=data)

    async def delete_node(self, node_id: str) -> dict[str, Any]:
        """Delete a single node by *node_id*."""
        return await self.send("delete_node", nodeId=node_id)

    async def delete_nodes(self, ids: list[str]) -> dict[str, Any]:
        """Delete multiple nodes by their IDs."""
        return await self.send("delete_nodes", nodeIds=ids)

    async def set_selection(self, **kwargs: Any) -> dict[str, Any]:
        """Set the current selection in the editor."""
        # The TypeScript handler expects a nested `selection` object
        selection: dict[str, Any] = {}
        key_map = {"building_id": "buildingId", "level_id": "levelId",
                    "zone_id": "zoneId", "selected_ids": "selectedIds"}
        for k, v in kwargs.items():
            selection[key_map.get(k, k)] = v
        return await self.send("set_selection", selection=selection)

    async def undo(self) -> dict[str, Any]:
        """Undo the last operation."""
        return await self.send("undo")

    async def clear(self) -> dict[str, Any]:
        """Clear the editor scene."""
        return await self.send("clear")

    async def save_scene(self, filepath: str) -> None:
        """Export current scene and save to a JSON file."""
        import pathlib
        resp = await self.send("export")
        data = resp.get("data", resp)
        pathlib.Path(filepath).write_text(json.dumps(data, indent=2))

    async def load_scene(self, filepath: str) -> dict[str, Any]:
        """Load a scene from a JSON file into the editor."""
        import pathlib
        data = json.loads(pathlib.Path(filepath).read_text())
        return await self.send("import", nodes=data["nodes"], rootNodeIds=data["rootNodeIds"])

    async def read_assets(self, category: str | None = None) -> dict[str, Any]:
        """Read available assets, optionally filtered by *category*."""
        params: dict[str, Any] = {}
        if category is not None:
            params["category"] = category
        return await self.send("read_assets", **params)
