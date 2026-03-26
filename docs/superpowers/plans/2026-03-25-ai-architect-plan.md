# AI Architect System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI-driven multi-agent system that generates 3D buildings in the Pascal Editor from natural language prompts.

**Architecture:** A WebSocket bridge in the editor browser tab exposes all Zustand store operations. A Python LangGraph pipeline (Architect -> Floor Planner -> Builder -> Furnisher) processes the user's prompt and sends structured commands over WebSocket. The editor renders results live.

**Tech Stack:** Python 3.11+, LangChain/LangGraph, WebSocket (ws), Next.js 16, React 19, Zustand, Zod, Three.js

**Spec:** `docs/superpowers/specs/2026-03-25-ai-architect-design.md`

---

## File Map

### Editor-Side (WebSocket Bridge)

| File | Action | Responsibility |
|------|--------|---------------|
| `editor/apps/editor/app/page.tsx` | Modify | Mount `<BridgeProvider>` alongside `<Editor>` |
| `editor/apps/editor/components/bridge/command-handler.ts` | Create | Maps JSON commands to Zustand store actions |
| `editor/apps/editor/components/bridge/bridge-provider.tsx` | Create | Client-side WebSocket server component |
| `editor/apps/editor/components/bridge/types.ts` | Create | Command/response type definitions |

### Python-Side (LangGraph Pipeline)

| File | Action | Responsibility |
|------|--------|---------------|
| `architectbot/pyproject.toml` | Create | Python package config with dependencies |
| `architectbot/architect/__init__.py` | Create | Package init |
| `architectbot/architect/__main__.py` | Create | CLI entry point with click |
| `architectbot/architect/config.py` | Create | Model registry, defaults |
| `architectbot/architect/state.py` | Create | BuildState TypedDict |
| `architectbot/architect/client.py` | Create | WebSocket client for editor communication |
| `architectbot/architect/graph.py` | Create | LangGraph state machine |
| `architectbot/architect/agents/__init__.py` | Create | Agents package |
| `architectbot/architect/agents/architect.py` | Create | Architect agent (planning) |
| `architectbot/architect/agents/floor_planner.py` | Create | Floor planner agent (coordinates) |
| `architectbot/architect/agents/builder.py` | Create | Builder agent (API execution) |
| `architectbot/architect/agents/furnisher.py` | Create | Furnisher agent (furniture) |
| `architectbot/architect/tools/__init__.py` | Create | Tools package |
| `architectbot/architect/tools/editor.py` | Create | LangChain @tool wrappers |
| `architectbot/architect/prompts/architect.md` | Create | Architect agent system prompt |
| `architectbot/architect/prompts/floor_planner.md` | Create | Floor planner system prompt |
| `architectbot/architect/prompts/builder.md` | Create | Builder system prompt |
| `architectbot/architect/prompts/furnisher.md` | Create | Furnisher system prompt |

### Tests

| File | Action | Responsibility |
|------|--------|---------------|
| `architectbot/tests/test_client.py` | Create | WebSocket client tests |
| `architectbot/tests/test_state.py` | Create | BuildState tests |
| `architectbot/tests/test_graph.py` | Create | LangGraph pipeline tests |
| `architectbot/tests/test_tools.py` | Create | Editor tool wrapper tests |

---

## Task 1: Editor WebSocket Bridge - Types and Command Handler

**Files:**
- Create: `editor/apps/editor/components/bridge/types.ts`
- Create: `editor/apps/editor/components/bridge/command-handler.ts`

- [ ] **Step 1: Create command/response type definitions**

Create `editor/apps/editor/components/bridge/types.ts`:

```typescript
// Command types for the WebSocket bridge protocol
export type BridgeCommand =
  // State reading
  | { cmd: 'read_state'; id: string }
  | { cmd: 'read_nodes'; id: string; type?: string }
  | { cmd: 'read_node'; id: string; nodeId: string }
  | { cmd: 'read_viewer'; id: string }
  | { cmd: 'read_editor'; id: string }
  | { cmd: 'read_assets'; id: string; category?: string }
  // Node CRUD
  | { cmd: 'create_node'; id: string; node: Record<string, unknown>; parentId?: string }
  | { cmd: 'create_nodes'; id: string; ops: { node: Record<string, unknown>; parentId?: string }[] }
  | { cmd: 'update_node'; id: string; nodeId: string; data: Record<string, unknown> }
  | { cmd: 'update_nodes'; id: string; updates: { id: string; data: Record<string, unknown> }[] }
  | { cmd: 'delete_node'; id: string; nodeId: string }
  | { cmd: 'delete_nodes'; id: string; ids: string[] }
  // Viewer/Editor control
  | { cmd: 'set_selection'; id: string; buildingId?: string; levelId?: string; zoneId?: string; selectedIds?: string[] }
  | { cmd: 'set_camera'; id: string; cameraMode?: string; levelMode?: string; wallMode?: string }
  | { cmd: 'set_display'; id: string; showScans?: boolean; showGuides?: boolean; showGrid?: boolean; theme?: string; unit?: string }
  | { cmd: 'set_tool'; id: string; tool?: string; phase?: string; mode?: string }
  // Actions
  | { cmd: 'undo'; id: string }
  | { cmd: 'redo'; id: string }
  | { cmd: 'clear'; id: string }
  | { cmd: 'export'; id: string }
  // Collections
  | { cmd: 'create_collection'; id: string; name: string; nodeIds?: string[] }
  | { cmd: 'update_collection'; id: string; collectionId: string; data: Record<string, unknown> }
  | { cmd: 'delete_collection'; id: string; collectionId: string }
  | { cmd: 'add_to_collection'; id: string; collectionId: string; nodeId: string }
  | { cmd: 'remove_from_collection'; id: string; collectionId: string; nodeId: string }

export type BridgeResponse = {
  id: string
  ok: boolean
  data?: unknown
  error?: string
}
```

- [ ] **Step 2: Create command handler**

Create `editor/apps/editor/components/bridge/command-handler.ts`:

```typescript
import { useScene } from '@pascal-app/core'
import { useViewer } from '@pascal-app/viewer'
import { useEditor } from '@pascal-app/editor'
import { CATALOG_ITEMS } from '../ui/item-catalog/catalog-items'
import type { BridgeCommand, BridgeResponse } from './types'

export function handleCommand(cmd: BridgeCommand): BridgeResponse {
  try {
    switch (cmd.cmd) {
      // --- State reading ---
      case 'read_state': {
        const scene = useScene.getState()
        const viewer = useViewer.getState()
        const editor = useEditor.getState()
        return {
          id: cmd.id,
          ok: true,
          data: {
            nodes: scene.nodes,
            rootNodeIds: scene.rootNodeIds,
            collections: scene.collections,
            viewer: {
              selection: viewer.selection,
              cameraMode: viewer.cameraMode,
              theme: viewer.theme,
              unit: viewer.unit,
              levelMode: viewer.levelMode,
              wallMode: viewer.wallMode,
              showScans: viewer.showScans,
              showGuides: viewer.showGuides,
              showGrid: viewer.showGrid,
            },
            editor: {
              phase: editor.phase,
              mode: editor.mode,
              tool: editor.tool,
              structureLayer: editor.structureLayer,
            },
          },
        }
      }

      case 'read_nodes': {
        const nodes = useScene.getState().nodes
        if (cmd.type) {
          const filtered: Record<string, unknown> = {}
          for (const [id, node] of Object.entries(nodes)) {
            if ((node as any).type === cmd.type) filtered[id] = node
          }
          return { id: cmd.id, ok: true, data: filtered }
        }
        return { id: cmd.id, ok: true, data: nodes }
      }

      case 'read_node': {
        const node = useScene.getState().nodes[cmd.nodeId]
        if (!node) return { id: cmd.id, ok: false, error: `Node ${cmd.nodeId} not found` }
        return { id: cmd.id, ok: true, data: node }
      }

      case 'read_viewer': {
        const v = useViewer.getState()
        return {
          id: cmd.id,
          ok: true,
          data: {
            selection: v.selection,
            cameraMode: v.cameraMode,
            theme: v.theme,
            unit: v.unit,
            levelMode: v.levelMode,
            wallMode: v.wallMode,
            showScans: v.showScans,
            showGuides: v.showGuides,
            showGrid: v.showGrid,
          },
        }
      }

      case 'read_editor': {
        const e = useEditor.getState()
        return {
          id: cmd.id,
          ok: true,
          data: {
            phase: e.phase,
            mode: e.mode,
            tool: e.tool,
            structureLayer: e.structureLayer,
            catalogCategory: e.catalogCategory,
          },
        }
      }

      case 'read_assets': {
        const items = cmd.category
          ? CATALOG_ITEMS.filter((i) => i.category === cmd.category)
          : CATALOG_ITEMS
        return { id: cmd.id, ok: true, data: items }
      }

      // --- Node CRUD ---
      case 'create_node': {
        const beforeIds = new Set(Object.keys(useScene.getState().nodes))
        useScene.getState().createNode(cmd.node as any, cmd.parentId as any)
        const afterNodes = useScene.getState().nodes
        const newId = Object.keys(afterNodes).find((id) => !beforeIds.has(id))
        if (!newId) return { id: cmd.id, ok: false, error: 'Node creation failed - no new ID found' }
        return { id: cmd.id, ok: true, data: { nodeId: newId, node: afterNodes[newId] } }
      }

      case 'create_nodes': {
        const beforeIds = new Set(Object.keys(useScene.getState().nodes))
        useScene.getState().createNodes(cmd.ops as any)
        const afterNodes = useScene.getState().nodes
        const newIds = Object.keys(afterNodes).filter((id) => !beforeIds.has(id))
        return { id: cmd.id, ok: true, data: { nodeIds: newIds } }
      }

      case 'update_node': {
        useScene.getState().updateNode(cmd.nodeId as any, cmd.data as any)
        return { id: cmd.id, ok: true, data: { nodeId: cmd.nodeId } }
      }

      case 'update_nodes': {
        useScene.getState().updateNodes(cmd.updates as any)
        return { id: cmd.id, ok: true }
      }

      case 'delete_node': {
        useScene.getState().deleteNode(cmd.nodeId as any)
        return { id: cmd.id, ok: true }
      }

      case 'delete_nodes': {
        useScene.getState().deleteNodes(cmd.ids as any)
        return { id: cmd.id, ok: true }
      }

      // --- Viewer/Editor control ---
      case 'set_selection': {
        const { id: _, cmd: __, ...selection } = cmd
        useViewer.getState().setSelection(selection as any)
        return { id: cmd.id, ok: true }
      }

      case 'set_camera': {
        const v = useViewer.getState()
        if (cmd.cameraMode) v.setCameraMode(cmd.cameraMode as any)
        if (cmd.levelMode) v.setLevelMode(cmd.levelMode as any)
        if (cmd.wallMode) v.setWallMode(cmd.wallMode as any)
        return { id: cmd.id, ok: true }
      }

      case 'set_display': {
        const v = useViewer.getState()
        if (cmd.showScans !== undefined) v.setShowScans(cmd.showScans)
        if (cmd.showGuides !== undefined) v.setShowGuides(cmd.showGuides)
        if (cmd.showGrid !== undefined) v.setShowGrid(cmd.showGrid)
        if (cmd.theme) v.setTheme(cmd.theme as any)
        if (cmd.unit) v.setUnit(cmd.unit as any)
        return { id: cmd.id, ok: true }
      }

      case 'set_tool': {
        const e = useEditor.getState()
        if (cmd.phase) e.setPhase(cmd.phase as any)
        if (cmd.mode) e.setMode(cmd.mode as any)
        if (cmd.tool !== undefined) e.setTool(cmd.tool as any)
        return { id: cmd.id, ok: true }
      }

      // --- Actions ---
      case 'undo': {
        useScene.temporal.getState().undo()
        return { id: cmd.id, ok: true }
      }

      case 'redo': {
        useScene.temporal.getState().redo()
        return { id: cmd.id, ok: true }
      }

      case 'clear': {
        useScene.getState().clearScene()
        return { id: cmd.id, ok: true }
      }

      case 'export': {
        const scene = useScene.getState()
        return {
          id: cmd.id,
          ok: true,
          data: { nodes: scene.nodes, rootNodeIds: scene.rootNodeIds },
        }
      }

      // --- Collections ---
      case 'create_collection': {
        const colId = useScene.getState().createCollection(cmd.name, cmd.nodeIds as any)
        return { id: cmd.id, ok: true, data: { collectionId: colId } }
      }

      case 'update_collection': {
        useScene.getState().updateCollection(cmd.collectionId as any, cmd.data as any)
        return { id: cmd.id, ok: true }
      }

      case 'delete_collection': {
        useScene.getState().deleteCollection(cmd.collectionId as any)
        return { id: cmd.id, ok: true }
      }

      case 'add_to_collection': {
        useScene.getState().addToCollection(cmd.collectionId as any, cmd.nodeId as any)
        return { id: cmd.id, ok: true }
      }

      case 'remove_from_collection': {
        useScene.getState().removeFromCollection(cmd.collectionId as any, cmd.nodeId as any)
        return { id: cmd.id, ok: true }
      }

      default:
        return { id: (cmd as any).id, ok: false, error: `Unknown command: ${(cmd as any).cmd}` }
    }
  } catch (error) {
    return {
      id: (cmd as any).id ?? 'unknown',
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd editor && npx tsc --noEmit --project apps/editor/tsconfig.json 2>&1 | head -20`
Expected: No errors related to bridge files (some pre-existing warnings may appear)

- [ ] **Step 4: Commit**

```bash
git add apps/editor/components/bridge/
git commit -m "feat: add WebSocket bridge command handler and types"
```

---

## Task 2: Editor WebSocket Bridge - BridgeProvider Component

**Files:**
- Create: `editor/apps/editor/components/bridge/bridge-provider.tsx`
- Modify: `editor/apps/editor/app/page.tsx`

- [ ] **Step 1: Create BridgeProvider component**

Create `editor/apps/editor/components/bridge/bridge-provider.tsx`:

```tsx
'use client'

import { useEffect, useRef } from 'react'
import { handleCommand } from './command-handler'
import type { BridgeCommand } from './types'

const WS_PORT = 3100

export function BridgeProvider() {
  const wsRef = useRef<WebSocket | null>(null)
  const serverRef = useRef<any>(null)

  useEffect(() => {
    // In the browser, we can't create a WebSocket server directly.
    // Instead, we connect to a lightweight relay server or use a
    // polling-based approach. For simplicity, we'll use a WebSocket
    // client that connects to a tiny Node.js relay bundled with the editor.
    //
    // Alternative: Use BroadcastChannel + a Next.js API route with SSE.
    //
    // For now, we set up a message listener on a WebSocket connection.
    // The Python client connects to the same relay server.

    let ws: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout>

    function connect() {
      try {
        ws = new WebSocket(`ws://localhost:${WS_PORT}`)
        wsRef.current = ws

        ws.onopen = () => {
          console.log('[Bridge] Connected to relay server')
          // Register as the editor client
          ws?.send(JSON.stringify({ type: 'register', role: 'editor' }))
        }

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'command') {
              const cmd = msg.payload as BridgeCommand
              const response = handleCommand(cmd)
              ws?.send(JSON.stringify({ type: 'response', payload: response }))
            }
          } catch (err) {
            console.error('[Bridge] Failed to handle message:', err)
          }
        }

        ws.onclose = () => {
          console.log('[Bridge] Disconnected, reconnecting in 3s...')
          reconnectTimer = setTimeout(connect, 3000)
        }

        ws.onerror = () => {
          ws?.close()
        }
      } catch {
        reconnectTimer = setTimeout(connect, 3000)
      }
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [])

  return null // Renderless component
}
```

- [ ] **Step 2: Mount BridgeProvider in page.tsx**

Modify `editor/apps/editor/app/page.tsx`:

```tsx
'use client'

import { Editor } from '@pascal-app/editor'
import { BridgeProvider } from '../components/bridge/bridge-provider'

export default function Home() {
  return (
    <div className="h-screen w-screen">
      <BridgeProvider />
      <Editor projectId="local-editor" />
    </div>
  )
}
```

- [ ] **Step 3: Verify editor still loads**

Run: `cd editor && bun dev`
Open `http://localhost:3002` in browser. Editor should load normally. Console should show `[Bridge] Connected to relay server` or `[Bridge] Disconnected, reconnecting in 3s...` (expected since relay isn't running yet).

- [ ] **Step 4: Commit**

```bash
git add apps/editor/components/bridge/bridge-provider.tsx apps/editor/app/page.tsx
git commit -m "feat: add BridgeProvider component and mount in editor"
```

---

## Task 3: WebSocket Relay Server

The browser cannot host a WebSocket server. We need a tiny Node.js relay that both the browser and Python connect to. This runs alongside `bun dev`.

**Files:**
- Create: `editor/apps/editor/bridge-relay.mjs`
- Modify: `editor/apps/editor/package.json` (add `bridge` script)

- [ ] **Step 1: Create relay server**

Create `editor/apps/editor/bridge-relay.mjs`:

```javascript
import { WebSocketServer } from 'ws'

const PORT = 3100
const wss = new WebSocketServer({ port: PORT })

let editorClient = null
const pythonClients = new Set()

wss.on('connection', (ws) => {
  let role = null

  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw.toString())

      if (msg.type === 'register') {
        role = msg.role
        if (role === 'editor') {
          editorClient = ws
          console.log('[Relay] Editor connected')
        } else if (role === 'python') {
          pythonClients.add(ws)
          console.log(`[Relay] Python client connected (${pythonClients.size} total)`)
        }
        return
      }

      // Python -> Editor: forward command
      if (msg.type === 'command' && role === 'python') {
        if (editorClient && editorClient.readyState === 1) {
          editorClient.send(JSON.stringify(msg))
        } else {
          ws.send(JSON.stringify({
            type: 'response',
            payload: { id: msg.payload?.id, ok: false, error: 'Editor not connected' },
          }))
        }
        return
      }

      // Editor -> Python: forward response
      if (msg.type === 'response' && role === 'editor') {
        const responseId = msg.payload?.id
        for (const client of pythonClients) {
          if (client.readyState === 1) {
            client.send(JSON.stringify(msg))
          }
        }
        return
      }
    } catch (err) {
      console.error('[Relay] Parse error:', err.message)
    }
  })

  ws.on('close', () => {
    if (role === 'editor') {
      editorClient = null
      console.log('[Relay] Editor disconnected')
    } else if (role === 'python') {
      pythonClients.delete(ws)
      console.log(`[Relay] Python client disconnected (${pythonClients.size} remaining)`)
    }
  })
})

console.log(`[Relay] WebSocket relay running on ws://localhost:${PORT}`)
```

- [ ] **Step 2: Add ws dependency and bridge script**

Run: `cd editor/apps/editor && bun add ws`

Modify `editor/apps/editor/package.json` scripts section, add:
```json
"bridge": "node bridge-relay.mjs"
```

- [ ] **Step 3: Test relay starts**

Run: `cd editor/apps/editor && node bridge-relay.mjs &`
Expected: `[Relay] WebSocket relay running on ws://localhost:3100`

Kill it after testing.

- [ ] **Step 4: Test editor connects to relay**

Terminal 1: `cd editor/apps/editor && node bridge-relay.mjs`
Terminal 2: `cd editor && bun dev`
Open `http://localhost:3002`

Expected in relay terminal: `[Relay] Editor connected`
Expected in browser console: `[Bridge] Connected to relay server`

- [ ] **Step 5: Commit**

```bash
git add apps/editor/bridge-relay.mjs apps/editor/package.json
git commit -m "feat: add WebSocket relay server for bridge communication"
```

---

## Task 4: Python Package Setup

**Files:**
- Create: `architectbot/pyproject.toml`
- Create: `architectbot/architect/__init__.py`
- Create: `architectbot/architect/state.py`
- Create: `architectbot/architect/config.py`

- [ ] **Step 1: Create pyproject.toml**

Create `architectbot/pyproject.toml`:

```toml
[project]
name = "architect"
version = "0.1.0"
description = "AI-powered building generator for Pascal Editor"
requires-python = ">=3.11"
dependencies = [
    "langchain-core>=0.3",
    "langgraph>=0.4",
    "langchain-anthropic>=0.3",
    "langchain-openai>=0.3",
    "websockets>=14.0",
    "click>=8.1",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create state.py**

Create `architectbot/architect/state.py`:

```python
from __future__ import annotations
from typing import TypedDict


class BuildState(TypedDict, total=False):
    # Input
    prompt: str
    model_name: str
    editor_url: str  # http://localhost:3002
    ws_url: str  # ws://localhost:3100

    # Architect output
    architect_spec: dict | None

    # Floor tracking
    current_floor_index: int
    total_floors: int

    # Floor Planner output (accumulated)
    floor_plans: list[dict]

    # Builder output (accumulated)
    built_node_ids: list[str]
    building_id: str | None
    level_ids: list[str]
    wall_id_map: dict[int, list[str]]  # floor_index -> ordered wall_ids

    # Errors
    errors: list[str]
```

- [ ] **Step 3: Create config.py**

Create `architectbot/architect/config.py`:

```python
from __future__ import annotations

from langchain_core.language_models import BaseChatModel


def get_model(model_name: str) -> BaseChatModel:
    """Resolve a model name to a LangChain chat model instance."""
    if model_name.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name)
    elif model_name.startswith("gpt") or model_name.startswith("o"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name)
    else:
        raise ValueError(
            f"Unknown model: {model_name}. "
            f"Supported prefixes: claude-*, gpt-*, o*"
        )


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_WS_URL = "ws://localhost:3100"
DEFAULT_EDITOR_URL = "http://localhost:3002"
```

- [ ] **Step 4: Create __init__.py**

Create `architectbot/architect/__init__.py`:

```python
"""AI Architect - generates 3D buildings from natural language prompts."""
```

- [ ] **Step 5: Install in dev mode and verify**

Run: `cd architectbot && pip install -e ".[dev]"`
Run: `python -c "from architect.state import BuildState; print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml architect/
git commit -m "feat: python package setup with state, config, and dependencies"
```

---

## Task 5: Python WebSocket Client

**Files:**
- Create: `architectbot/architect/client.py`
- Create: `architectbot/tests/__init__.py`
- Create: `architectbot/tests/test_client.py`

- [ ] **Step 1: Write failing test for client**

Create `architectbot/tests/__init__.py` (empty file).

Create `architectbot/tests/test_client.py`:

```python
import pytest
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
```

Run: `cd architectbot && python -m pytest tests/test_client.py -v`
Expected: FAIL (module not found)

- [ ] **Step 2: Implement WebSocket client**

Create `architectbot/architect/client.py`:

```python
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection


class EditorClient:
    """WebSocket client that sends commands to the Pascal Editor via relay."""

    def __init__(self, ws_url: str = "ws://localhost:3100"):
        self.ws_url = ws_url
        self._ws: ClientConnection | None = None
        self._pending: dict[str, asyncio.Future[dict]] = {}

    def _build_message(self, cmd: str, params: dict[str, Any]) -> dict:
        msg_id = uuid.uuid4().hex[:12]
        return {
            "type": "command",
            "payload": {"cmd": cmd, "id": msg_id, **params},
        }

    async def connect(self) -> None:
        self._ws = await websockets.connect(self.ws_url)
        await self._ws.send(json.dumps({"type": "register", "role": "python"}))
        # Start listener task
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                if msg.get("type") == "response":
                    payload = msg["payload"]
                    msg_id = payload.get("id")
                    if msg_id in self._pending:
                        self._pending[msg_id].set_result(payload)
        except websockets.ConnectionClosed:
            pass

    async def send(self, cmd: str, **params: Any) -> dict:
        """Send a command and wait for the response."""
        assert self._ws is not None, "Not connected. Call connect() first."
        msg = self._build_message(cmd, params)
        msg_id = msg["payload"]["id"]

        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = future

        await self._ws.send(json.dumps(msg))
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
        finally:
            self._pending.pop(msg_id, None)

        if not result.get("ok"):
            raise RuntimeError(f"Command {cmd} failed: {result.get('error')}")
        return result

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None
        if hasattr(self, "_listener_task"):
            self._listener_task.cancel()

    # --- Convenience methods ---

    async def read_state(self) -> dict:
        resp = await self.send("read_state")
        return resp.get("data", {})

    async def read_nodes(self, node_type: str | None = None) -> dict:
        params = {}
        if node_type:
            params["type"] = node_type
        resp = await self.send("read_nodes", **params)
        return resp.get("data", {})

    async def create_node(self, node: dict, parent_id: str | None = None) -> dict:
        params: dict[str, Any] = {"node": node}
        if parent_id:
            params["parentId"] = parent_id
        resp = await self.send("create_node", **params)
        return resp.get("data", {})

    async def create_nodes(self, ops: list[dict]) -> dict:
        resp = await self.send("create_nodes", ops=ops)
        return resp.get("data", {})

    async def update_node(self, node_id: str, data: dict) -> dict:
        resp = await self.send("update_node", nodeId=node_id, data=data)
        return resp.get("data", {})

    async def delete_node(self, node_id: str) -> dict:
        return await self.send("delete_node", nodeId=node_id)

    async def delete_nodes(self, ids: list[str]) -> dict:
        return await self.send("delete_nodes", ids=ids)

    async def set_selection(self, **kwargs: Any) -> dict:
        return await self.send("set_selection", **kwargs)

    async def undo(self) -> dict:
        return await self.send("undo")

    async def clear(self) -> dict:
        return await self.send("clear")

    async def read_assets(self, category: str | None = None) -> list:
        params = {}
        if category:
            params["category"] = category
        resp = await self.send("read_assets", **params)
        return resp.get("data", [])
```

- [ ] **Step 3: Run tests**

Run: `cd architectbot && python -m pytest tests/test_client.py -v`
Expected: 2 tests PASS

- [ ] **Step 4: Commit**

```bash
git add architect/client.py tests/
git commit -m "feat: WebSocket client for editor communication"
```

---

## Task 6: LangChain Tool Wrappers

**Files:**
- Create: `architectbot/architect/tools/__init__.py`
- Create: `architectbot/architect/tools/editor.py`

- [ ] **Step 1: Create tools package**

Create `architectbot/architect/tools/__init__.py` (empty file).

- [ ] **Step 2: Create editor tool wrappers**

Create `architectbot/architect/tools/editor.py`:

```python
from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import tool

from architect.client import EditorClient

# Global client reference - set by the graph before agents run
_client: EditorClient | None = None


def set_client(client: EditorClient) -> None:
    global _client
    _client = client


def _run(coro: Any) -> Any:
    """Run async function from sync tool context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # If a loop is already running (e.g., inside LangChain), use a thread
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()


@tool
def read_state() -> dict:
    """Read the full current state of the editor: all nodes, viewer settings, editor settings."""
    assert _client, "Client not connected"
    return _run(_client.read_state())


@tool
def read_nodes(node_type: str | None = None) -> dict:
    """Read all nodes, optionally filtered by type (wall, slab, zone, item, door, window, etc.)."""
    assert _client, "Client not connected"
    return _run(_client.read_nodes(node_type))


@tool
def create_wall(level_id: str, start: list[float], end: list[float],
                thickness: float = 0.1, height: float = 2.5,
                front_side: str = "unknown", back_side: str = "unknown") -> dict:
    """Create a wall on a level. start/end are [x, z] coordinates in meters.
    front_side/back_side: 'interior', 'exterior', or 'unknown'."""
    assert _client, "Client not connected"
    node = {
        "type": "wall",
        "start": start,
        "end": end,
        "thickness": thickness,
        "height": height,
        "frontSide": front_side,
        "backSide": back_side,
    }
    return _run(_client.create_node(node, level_id))


@tool
def create_slab(level_id: str, polygon: list[list[float]],
                elevation: float = 0.05) -> dict:
    """Create a floor slab. polygon is list of [x, z] points in meters."""
    assert _client, "Client not connected"
    node = {"type": "slab", "polygon": polygon, "elevation": elevation}
    return _run(_client.create_node(node, level_id))


@tool
def create_ceiling(level_id: str, polygon: list[list[float]],
                   height: float = 2.5) -> dict:
    """Create a ceiling. polygon is list of [x, z] points in meters."""
    assert _client, "Client not connected"
    node = {"type": "ceiling", "polygon": polygon, "height": height}
    return _run(_client.create_node(node, level_id))


@tool
def create_zone(level_id: str, name: str, polygon: list[list[float]],
                color: str = "#3b82f6") -> dict:
    """Create a named zone (room). polygon is list of [x, z] points in meters."""
    assert _client, "Client not connected"
    node = {"type": "zone", "name": name, "polygon": polygon, "color": color}
    return _run(_client.create_node(node, level_id))


def _wall_local_x(wall_start: list[float], wall_end: list[float],
                  position_along_wall: float) -> float:
    """Convert distance-from-wall-start to wall-local x coordinate (centered on wall).
    Wall-local x=0 is the center of the wall."""
    import math
    wall_length = math.sqrt(
        (wall_end[0] - wall_start[0]) ** 2 + (wall_end[1] - wall_start[1]) ** 2
    )
    return position_along_wall - (wall_length / 2)


@tool
def create_door(wall_id: str, wall_start: list[float], wall_end: list[float],
                position_along_wall: float, width: float = 0.9,
                height: float = 2.1, side: str = "front",
                hinges_side: str = "left",
                swing_direction: str = "inward") -> dict:
    """Create a door on a wall. position_along_wall is distance in meters from wall START.
    wall_start/wall_end are the [x,z] coords of the wall (needed for coordinate conversion).
    IMPORTANT: parentId MUST be the wall_id for CSG cutouts to work."""
    assert _client, "Client not connected"
    x_local = _wall_local_x(wall_start, wall_end, position_along_wall)
    node = {
        "type": "door",
        "position": [x_local, height / 2, 0],
        "rotation": [0, 0, 0],
        "wallId": wall_id,
        "side": side,
        "width": width,
        "height": height,
        "hingesSide": hinges_side,
        "swingDirection": swing_direction,
    }
    return _run(_client.create_node(node, wall_id))


@tool
def create_window(wall_id: str, wall_start: list[float], wall_end: list[float],
                  position_along_wall: float, width: float = 1.5,
                  height: float = 1.5, side: str = "front",
                  sill_height: float = 0.9) -> dict:
    """Create a window on a wall. position_along_wall is distance in meters from wall START.
    wall_start/wall_end are the [x,z] coords of the wall (needed for coordinate conversion).
    sill_height is the bottom of the window from floor.
    IMPORTANT: parentId MUST be the wall_id for CSG cutouts to work."""
    assert _client, "Client not connected"
    x_local = _wall_local_x(wall_start, wall_end, position_along_wall)
    node = {
        "type": "window",
        "position": [x_local, sill_height + height / 2, 0],
        "rotation": [0, 0, 0],
        "wallId": wall_id,
        "side": side,
        "width": width,
        "height": height,
    }
    return _run(_client.create_node(node, wall_id))


@tool
def create_roof(level_id: str, roof_type: str = "gable", width: float = 8,
                depth: float = 6, roof_height: float = 2.5,
                wall_height: float = 0.5) -> dict:
    """Create a roof on the top level. Creates both RoofNode (container) and RoofSegmentNode (geometry)."""
    assert _client, "Client not connected"
    # Step 1: Create RoofNode as child of level
    roof_node = {
        "type": "roof",
        "position": [0, 0, 0],
        "rotation": 0,
    }
    roof_result = _run(_client.create_node(roof_node, level_id))
    roof_id = roof_result.get("nodeId")

    # Step 2: Create RoofSegmentNode as child of roof
    segment_node = {
        "type": "roof-segment",
        "roofType": roof_type,
        "position": [0, 0, 0],
        "rotation": 0,
        "width": width,
        "depth": depth,
        "wallHeight": wall_height,
        "roofHeight": roof_height,
        "wallThickness": 0.1,
        "deckThickness": 0.1,
        "overhang": 0.3,
        "shingleThickness": 0.05,
    }
    segment_result = _run(_client.create_node(segment_node, roof_id))
    return {"roofId": roof_id, "segmentId": segment_result.get("nodeId")}


@tool
def create_level(building_id: str, level_number: int) -> dict:
    """Create a new level (floor) in a building."""
    assert _client, "Client not connected"
    node = {"type": "level", "level": level_number}
    return _run(_client.create_node(node, building_id))


@tool
def create_item(parent_id: str, asset_id: str, asset_name: str,
                asset_src: str, asset_category: str,
                dimensions: list[float],
                position: list[float], rotation: list[float] | None = None,
                wall_id: str | None = None,
                wall_t: float | None = None,
                side: str | None = None) -> dict:
    """Create a furniture/fixture item. parent_id is the level (floor items),
    wall (wall items), or ceiling (ceiling items)."""
    assert _client, "Client not connected"
    node: dict[str, Any] = {
        "type": "item",
        "position": position,
        "rotation": rotation or [0, 0, 0],
        "scale": [1, 1, 1],
        "asset": {
            "id": asset_id,
            "category": asset_category,
            "name": asset_name,
            "thumbnail": "",
            "src": asset_src,
            "dimensions": dimensions,
            "offset": [0, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
        },
    }
    if wall_id:
        node["wallId"] = wall_id
    if wall_t is not None:
        node["wallT"] = wall_t
    if side:
        node["side"] = side
    return _run(_client.create_node(node, parent_id))


@tool
def read_assets(category: str | None = None) -> list:
    """Read available furniture/fixture assets from the editor catalog."""
    assert _client, "Client not connected"
    return _run(_client.read_assets(category))


@tool
def select_level(level_id: str) -> dict:
    """Focus the editor viewport on a specific level."""
    assert _client, "Client not connected"
    return _run(_client.set_selection(levelId=level_id))


@tool
def undo() -> dict:
    """Undo the last action in the editor."""
    assert _client, "Client not connected"
    return _run(_client.undo())


@tool
def clear_scene() -> dict:
    """Clear the entire scene. Note: this recreates the default Site > Building > Level hierarchy."""
    assert _client, "Client not connected"
    return _run(_client.clear())
```

- [ ] **Step 3: Verify imports**

Run: `cd architectbot && python -c "from architect.tools.editor import read_state, create_wall; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add architect/tools/
git commit -m "feat: LangChain tool wrappers for editor WebSocket commands"
```

---

## Task 7: Agent System Prompts

**Files:**
- Create: `architectbot/architect/prompts/architect.md`
- Create: `architectbot/architect/prompts/floor_planner.md`
- Create: `architectbot/architect/prompts/builder.md`
- Create: `architectbot/architect/prompts/furnisher.md`

- [ ] **Step 1: Create architect system prompt**

Create `architectbot/architect/prompts/architect.md`:

```markdown
You are an architectural planner. Given a natural language description of a building, produce a structured JSON specification.

## Output Format

Return ONLY valid JSON (no markdown fences, no explanation):

{
  "style": "modern|traditional|industrial|minimalist",
  "floors": <number>,
  "buildingFootprint": [<width_meters>, <depth_meters>],
  "exteriorWallHeight": <meters, typically 2.5-3.0>,
  "roofType": "gable|hip|flat|shed",
  "levels": [
    {
      "level": <0-indexed floor number>,
      "name": "<Ground Floor|First Floor|etc>",
      "rooms": [
        {
          "type": "<living|kitchen|bedroom|master-bedroom|bathroom|hallway|office|garage|dining|laundry|storage|closet>",
          "approxArea": <square meters>,
          "position": [<x_centroid>, <z_centroid>]
        }
      ]
    }
  ]
}

## Design Rules

1. Room sizes (approximate): bedroom 12-20m2, master-bedroom 16-25m2, bathroom 4-8m2, kitchen 10-20m2, living 20-35m2, hallway 4-10m2, dining 10-16m2, garage 18-30m2
2. Every floor must have a hallway connecting rooms
3. Bathrooms should be adjacent to bedrooms when possible
4. Kitchen should be near dining/living areas
5. Building footprint should be rectangular or L-shaped
6. Position centroids relative to origin [0,0], using the full footprint area
7. Ensure total room areas approximately match the footprint area
8. Upper floors should have similar or smaller footprint than ground floor
```

- [ ] **Step 2: Create floor planner system prompt**

Create `architectbot/architect/prompts/floor_planner.md`:

```markdown
You are a floor plan engineer. Given an architect's room specification for ONE floor, produce exact 2D wall coordinates, room polygons, and door/window placements.

## Coordinate System

- Units: meters
- X axis: east (positive = right)
- Z axis: south (positive = down)
- All coordinates should be aligned to 0.5m grid (multiples of 0.5)
- Origin [0, 0] is the top-left corner of the building

## Output Format

Return ONLY valid JSON (no markdown fences):

{
  "level_index": <0-indexed>,
  "walls": [
    {"start": [x, z], "end": [x, z], "thickness": 0.2, "height": 2.8}
  ],
  "slabs": [
    {"polygon": [[x, z], ...], "elevation": 0.05}
  ],
  "ceilings": [
    {"polygon": [[x, z], ...], "height": 2.5}
  ],
  "zones": [
    {"name": "Room Name", "polygon": [[x, z], ...], "color": "#hex"}
  ],
  "doors": [
    {"wall_index": <index into walls array>, "position_along_wall": <meters from wall start>, "width": 0.9, "height": 2.1, "side": "front"}
  ],
  "windows": [
    {"wall_index": <index into walls array>, "position_along_wall": <meters from wall start>, "width": 1.5, "height": 1.5, "side": "front"}
  ],
  "roofs": []
}

## Wall Rules

1. Exterior walls: form a closed rectangular/L-shaped loop, thickness 0.2m
2. Interior walls: connect to exterior walls, thickness 0.1m
3. Wall height: match exteriorWallHeight from architect spec
4. Walls are defined by start and end points — they are straight line segments
5. Adjacent walls should share exact endpoints (no gaps)

## Door/Window Rules

1. position_along_wall: distance in meters from the wall's START point to the center of the door/window
2. Exterior doors: width 0.9m, placed on walls facing outside
3. Interior doors: width 0.8m, one per room connecting to hallway
4. Windows: only on exterior walls, width 1.2-1.8m
5. Minimum 0.5m clearance from wall endpoints
6. No overlapping doors/windows on the same wall

## Zone Rules

1. One zone per room
2. Zone polygons should match the interior of the room (inside the walls)
3. Zone colors: living=#3b82f6, kitchen=#f59e0b, bedroom=#8b5cf6, bathroom=#06b6d4, hallway=#6b7280, office=#10b981, dining=#ef4444, garage=#78716c

## Slab/Ceiling

1. One slab per floor, polygon matches building exterior
2. One ceiling per floor, same polygon, height = wall height
```

- [ ] **Step 3: Create builder system prompt**

Create `architectbot/architect/prompts/builder.md`:

```markdown
The builder agent is DETERMINISTIC — it does not use LLM reasoning.
It executes the floor plan step-by-step using Python code, not a ReAct agent.
Wall IDs are tracked in an ordered Python list for reliable door/window placement.
See `architect/agents/builder.py` for the implementation.
```

- [ ] **Step 4: Create furnisher system prompt**

Create `architectbot/architect/prompts/furnisher.md`:

```markdown
You are an interior furnisher. You read the zones (rooms) from the editor and place appropriate furniture using items from the asset catalog.

## Process

1. Call read_assets() to see all available furniture
2. Call read_state() to find all zones and their polygons
3. For each zone, determine what furniture to place based on the room name
4. Place items within the zone polygon, keeping 0.3m clearance from walls
5. Verify placements with read_state()

## Room Furniture Guide

- **Living Room**: sofa (center-back), coffee table (in front of sofa), TV unit (opposite sofa)
- **Bedroom**: bed (center-back wall), nightstand (beside bed), wardrobe (side wall)
- **Master Bedroom**: king bed (center), 2 nightstands, wardrobe, dresser
- **Kitchen**: dining table (center or side), chairs around table
- **Bathroom**: minimal — most fixtures are built-in
- **Hallway**: minimal — maybe a console table
- **Office**: desk (facing window if possible), office chair, bookshelf
- **Dining**: dining table (center), chairs around table

## Placement Rules

1. Items are placed as children of the LEVEL (floor-standing) unless they attach to a wall
2. Position is [x, y, z] in world coordinates (y is up, typically 0 for floor items)
3. Match furniture to available assets by name/category
4. If an exact asset isn't in the catalog, skip it — don't invent asset IDs
5. Rotate furniture to face sensible directions (0, 90, 180, or 270 degrees)

## Available Tools

- read_state() — get all nodes including zones
- read_assets(category) — get available furniture from catalog
- create_item(parent_id, asset_id, asset_name, asset_src, asset_category, dimensions, position, rotation, wall_id, wall_t, side)
```

- [ ] **Step 5: Commit**

```bash
git add architect/prompts/
git commit -m "feat: agent system prompts for architect, floor planner, builder, furnisher"
```

---

## Task 8: Agent Implementations

**Files:**
- Create: `architectbot/architect/agents/__init__.py`
- Create: `architectbot/architect/agents/architect.py`
- Create: `architectbot/architect/agents/floor_planner.py`
- Create: `architectbot/architect/agents/builder.py`
- Create: `architectbot/architect/agents/furnisher.py`

- [ ] **Step 1: Create agents package**

Create `architectbot/architect/agents/__init__.py` (empty file).

- [ ] **Step 2: Create architect agent**

Create `architectbot/architect/agents/architect.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from architect.state import BuildState

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "architect.md"


def architect_agent(state: BuildState, model: BaseChatModel) -> dict:
    """Plan the building structure from user prompt."""
    system_prompt = PROMPT_PATH.read_text()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["prompt"]),
    ]

    # Retry up to 2 times on invalid JSON
    for attempt in range(3):
        response = model.invoke(messages)
        content = response.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""

        try:
            # Strip markdown fences if present
            text = str(content).strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]
            spec = json.loads(text)
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
        except (json.JSONDecodeError, KeyError) as e:
            if attempt == 2:
                return {"errors": [f"Architect failed after 3 attempts: {e}"]}
            messages.append(HumanMessage(
                content=f"Invalid JSON. Error: {e}. Try again, return ONLY valid JSON."
            ))

    return {"errors": ["Architect failed unexpectedly"]}
```

- [ ] **Step 3: Create floor planner agent**

Create `architectbot/architect/agents/floor_planner.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from architect.state import BuildState

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "floor_planner.md"


def floor_planner_agent(state: BuildState, model: BaseChatModel) -> dict:
    """Convert one floor's room spec into exact 2D coordinates."""
    system_prompt = PROMPT_PATH.read_text()
    spec = state["architect_spec"]
    floor_idx = state["current_floor_index"]
    level_spec = spec["levels"][floor_idx]

    user_msg = json.dumps({
        "floor": level_spec,
        "buildingFootprint": spec.get("buildingFootprint", [10, 8]),
        "exteriorWallHeight": spec.get("exteriorWallHeight", 2.8),
        "roofType": spec.get("roofType", "gable"),
        "isTopFloor": floor_idx == state["total_floors"] - 1,
    }, indent=2)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_msg),
    ]

    for attempt in range(3):
        response = model.invoke(messages)
        content = response.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""

        try:
            text = str(content).strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]
            floor_plan = json.loads(text)
            floor_plan["level_index"] = floor_idx

            updated_plans = list(state.get("floor_plans", []))
            updated_plans.append(floor_plan)
            return {"floor_plans": updated_plans}
        except (json.JSONDecodeError, KeyError) as e:
            if attempt == 2:
                errors = list(state.get("errors", []))
                errors.append(f"Floor planner failed for floor {floor_idx}: {e}")
                return {"errors": errors}
            messages.append(HumanMessage(
                content=f"Invalid JSON. Error: {e}. Return ONLY valid JSON."
            ))

    return {"errors": state.get("errors", []) + ["Floor planner failed unexpectedly"]}
```

- [ ] **Step 4: Create builder agent**

Create `architectbot/architect/agents/builder.py`:

```python
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


def builder_agent(state: BuildState, model=None) -> dict:
    """Deterministic builder: executes floor plan step-by-step with no LLM reasoning.
    The floor plan already has exact coordinates — no AI decision-making needed here."""
    floor_idx = state["current_floor_index"]
    floor_plan = state["floor_plans"][floor_idx]
    building_id = state.get("building_id")
    level_ids = list(state.get("level_ids", []))
    built_ids = list(state.get("built_node_ids", []))
    wall_id_map = dict(state.get("wall_id_map", {}))
    errors = list(state.get("errors", []))

    # --- Step 1: Find or reuse building and level ---
    if not building_id or floor_idx == 0:
        # Read existing state to find default building/level
        scene = read_state.invoke({})
        nodes = scene.get("nodes", {})
        for nid, node in nodes.items():
            if node.get("type") == "building" and not building_id:
                building_id = nid
            if node.get("type") == "level" and floor_idx == 0:
                if nid not in level_ids:
                    level_ids.append(nid)

    # --- Step 2: Create level if needed ---
    if floor_idx == 0 and level_ids:
        level_id = level_ids[0]  # Reuse default level-0
        console.print(f"  -> Reusing existing level: {level_id}")
    else:
        result = create_level.invoke({
            "building_id": building_id, "level_number": floor_idx
        })
        level_id = result.get("nodeId")
        level_ids.append(level_id)
        built_ids.append(level_id)
        console.print(f"  -> Created level {floor_idx}: {level_id}")

    select_level.invoke({"level_id": level_id})

    # --- Step 3: Create slab ---
    for slab in floor_plan.get("slabs", []):
        try:
            result = create_slab.invoke({
                "level_id": level_id,
                "polygon": slab["polygon"],
                "elevation": slab.get("elevation", 0.05),
            })
            built_ids.append(result.get("nodeId", ""))
        except Exception as e:
            errors.append(f"Slab creation failed: {e}")

    # --- Step 4: Create walls (ordered — track IDs for door/window placement) ---
    floor_wall_ids = []
    walls_data = floor_plan.get("walls", [])
    for wall in walls_data:
        try:
            result = create_wall.invoke({
                "level_id": level_id,
                "start": wall["start"],
                "end": wall["end"],
                "thickness": wall.get("thickness", 0.1),
                "height": wall.get("height", 2.5),
                "front_side": wall.get("frontSide", "unknown"),
                "back_side": wall.get("backSide", "unknown"),
            })
            wall_id = result.get("nodeId", "")
            floor_wall_ids.append(wall_id)
            built_ids.append(wall_id)
        except Exception as e:
            floor_wall_ids.append("")  # Placeholder to keep indices aligned
            errors.append(f"Wall creation failed: {e}")

    console.print(f"  -> Created {len(floor_wall_ids)} walls")

    # --- Step 5: Create doors (lookup wall by index) ---
    for door in floor_plan.get("doors", []):
        try:
            wi = door["wall_index"]
            if wi >= len(floor_wall_ids) or not floor_wall_ids[wi]:
                errors.append(f"Door references invalid wall_index {wi}")
                continue
            wall_id = floor_wall_ids[wi]
            wall_data = walls_data[wi]
            result = create_door.invoke({
                "wall_id": wall_id,
                "wall_start": wall_data["start"],
                "wall_end": wall_data["end"],
                "position_along_wall": door["position_along_wall"],
                "width": door.get("width", 0.9),
                "height": door.get("height", 2.1),
                "side": door.get("side", "front"),
                "hinges_side": door.get("hinges_side", "left"),
                "swing_direction": door.get("swing_direction", "inward"),
            })
            built_ids.append(result.get("nodeId", ""))
        except Exception as e:
            errors.append(f"Door creation failed: {e}")

    # --- Step 6: Create windows (lookup wall by index) ---
    for window in floor_plan.get("windows", []):
        try:
            wi = window["wall_index"]
            if wi >= len(floor_wall_ids) or not floor_wall_ids[wi]:
                errors.append(f"Window references invalid wall_index {wi}")
                continue
            wall_id = floor_wall_ids[wi]
            wall_data = walls_data[wi]
            result = create_window.invoke({
                "wall_id": wall_id,
                "wall_start": wall_data["start"],
                "wall_end": wall_data["end"],
                "position_along_wall": window["position_along_wall"],
                "width": window.get("width", 1.5),
                "height": window.get("height", 1.5),
                "side": window.get("side", "front"),
                "sill_height": window.get("sill_height", 0.9),
            })
            built_ids.append(result.get("nodeId", ""))
        except Exception as e:
            errors.append(f"Window creation failed: {e}")

    # --- Step 7: Create ceiling ---
    for ceiling in floor_plan.get("ceilings", []):
        try:
            result = create_ceiling.invoke({
                "level_id": level_id,
                "polygon": ceiling["polygon"],
                "height": ceiling.get("height", 2.5),
            })
            built_ids.append(result.get("nodeId", ""))
        except Exception as e:
            errors.append(f"Ceiling creation failed: {e}")

    # --- Step 8: Create zones ---
    for zone in floor_plan.get("zones", []):
        try:
            result = create_zone.invoke({
                "level_id": level_id,
                "name": zone["name"],
                "polygon": zone["polygon"],
                "color": zone.get("color", "#3b82f6"),
            })
            built_ids.append(result.get("nodeId", ""))
        except Exception as e:
            errors.append(f"Zone creation failed: {e}")

    # --- Step 9: Create roof (top floor only) ---
    if floor_idx == state["total_floors"] - 1:
        for roof in floor_plan.get("roofs", []):
            try:
                result = create_roof.invoke({
                    "level_id": level_id,
                    "roof_type": roof.get("roof_type", "gable"),
                    "width": roof.get("width", 8),
                    "depth": roof.get("depth", 6),
                    "roof_height": roof.get("roof_height", 2.5),
                    "wall_height": roof.get("wall_height", 0.5),
                })
                built_ids.append(result.get("roofId", ""))
                built_ids.append(result.get("segmentId", ""))
            except Exception as e:
                errors.append(f"Roof creation failed: {e}")

    wall_id_map[floor_idx] = floor_wall_ids

    console.print(f"  -> Floor {floor_idx} complete: {len(built_ids)} total nodes")

    return {
        "built_node_ids": built_ids,
        "building_id": building_id,
        "level_ids": level_ids,
        "wall_id_map": wall_id_map,
        "current_floor_index": floor_idx + 1,  # INCREMENT for next iteration
        "errors": errors,
    }
```

- [ ] **Step 5: Create furnisher agent**

Create `architectbot/architect/agents/furnisher.py`:

```python
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent

from architect.state import BuildState
from architect.tools.editor import (
    create_item,
    read_assets,
    read_state,
)

from pathlib import Path
import json

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "furnisher.md"

FURNISHER_TOOLS = [read_state, read_assets, create_item]


def furnisher_agent(state: BuildState, model: BaseChatModel) -> dict:
    """Place furniture in all rooms based on zone types."""
    system_prompt = PROMPT_PATH.read_text()

    level_ids = state.get("level_ids", [])
    task_description = (
        f"Furnish all rooms in the building.\n"
        f"Level IDs to furnish: {level_ids}\n"
        f"First, call read_assets() to see available furniture.\n"
        f"Then call read_state() to find all zones and their polygons.\n"
        f"Place appropriate furniture in each room."
    )

    agent = create_react_agent(model, FURNISHER_TOOLS, prompt=system_prompt)
    result = agent.invoke({"messages": [("human", task_description)]})

    # Extract placed item IDs
    built_ids = list(state.get("built_node_ids", []))
    for msg in result.get("messages", []):
        if hasattr(msg, "content") and isinstance(msg.content, str):
            try:
                data = json.loads(msg.content)
                if isinstance(data, dict) and "nodeId" in data:
                    built_ids.append(data["nodeId"])
            except (json.JSONDecodeError, TypeError):
                pass

    return {"built_node_ids": built_ids}
```

- [ ] **Step 6: Verify imports**

Run: `cd architectbot && python -c "from architect.agents.architect import architect_agent; from architect.agents.builder import builder_agent; from architect.agents.furnisher import furnisher_agent; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add architect/agents/
git commit -m "feat: implement all four LangGraph agents"
```

---

## Task 9: LangGraph State Machine

**Files:**
- Create: `architectbot/architect/graph.py`

- [ ] **Step 1: Create graph.py**

Create `architectbot/architect/graph.py`:

```python
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph

from architect.agents.architect import architect_agent
from architect.agents.builder import builder_agent
from architect.agents.floor_planner import floor_planner_agent
from architect.agents.furnisher import furnisher_agent
from architect.state import BuildState


def check_floors_remaining(state: BuildState) -> str:
    """Route: more floors to build or move to furnishing."""
    if state.get("errors"):
        return "done"
    if state["current_floor_index"] < state["total_floors"]:
        return "more_floors"
    return "done"


def check_architect_success(state: BuildState) -> str:
    """Route: architect succeeded or failed."""
    if state.get("errors"):
        return "failed"
    return "success"


def build_graph(model: BaseChatModel) -> StateGraph:
    """Build the LangGraph state machine for the architect pipeline."""

    # Wrap agents to inject the model
    def _architect(state: BuildState) -> dict:
        return architect_agent(state, model)

    def _floor_planner(state: BuildState) -> dict:
        return floor_planner_agent(state, model)

    def _builder(state: BuildState) -> dict:
        return builder_agent(state)  # Deterministic — no LLM needed

    def _furnisher(state: BuildState) -> dict:
        return furnisher_agent(state, model)

    graph = StateGraph(BuildState)

    graph.add_node("architect", _architect)
    graph.add_node("floor_planner", _floor_planner)
    graph.add_node("builder", _builder)
    graph.add_node("furnisher", _furnisher)

    graph.set_entry_point("architect")

    graph.add_conditional_edges("architect", check_architect_success, {
        "success": "floor_planner",
        "failed": END,
    })

    graph.add_edge("floor_planner", "builder")

    graph.add_conditional_edges("builder", check_floors_remaining, {
        "more_floors": "floor_planner",
        "done": "furnisher",
    })

    graph.add_edge("furnisher", END)

    return graph


def compile_graph(model: BaseChatModel):
    """Compile the graph into a runnable."""
    graph = build_graph(model)
    return graph.compile()
```

- [ ] **Step 2: Verify graph compiles**

Run: `cd architectbot && python -c "
from architect.graph import build_graph
from unittest.mock import MagicMock
model = MagicMock()
g = build_graph(model)
print('Graph nodes:', list(g.nodes))
print('OK')
"`
Expected: `Graph nodes: ['architect', 'floor_planner', 'builder', 'furnisher']` then `OK`

- [ ] **Step 3: Commit**

```bash
git add architect/graph.py
git commit -m "feat: LangGraph state machine with per-floor loop"
```

---

## Task 10: CLI Entry Point

**Files:**
- Create: `architectbot/architect/__main__.py`

- [ ] **Step 1: Create CLI entry point**

Create `architectbot/architect/__main__.py`:

```python
from __future__ import annotations

import asyncio
import sys

import click
from rich.console import Console
from rich.panel import Panel

from architect.client import EditorClient
from architect.config import DEFAULT_EDITOR_URL, DEFAULT_MODEL, DEFAULT_WS_URL, get_model
from architect.graph import compile_graph
from architect.tools.editor import set_client

console = Console()


@click.command()
@click.option("--model", default=DEFAULT_MODEL, help="LLM model name")
@click.option("--prompt", required=True, help="Building description")
@click.option("--editor-url", default=DEFAULT_EDITOR_URL, help="Editor URL")
@click.option("--ws-url", default=DEFAULT_WS_URL, help="WebSocket relay URL")
@click.option("--verbose", is_flag=True, help="Show agent reasoning")
@click.option("--clear", is_flag=True, help="Clear existing scene first")
def main(
    model: str,
    prompt: str,
    editor_url: str,
    ws_url: str,
    verbose: bool,
    clear: bool,
) -> None:
    """Generate a 3D building in Pascal Editor from a text prompt."""
    console.print(Panel(
        f"[bold]AI Architect[/bold]\n"
        f"Model: {model}\n"
        f"Prompt: {prompt}\n"
        f"Editor: {editor_url}",
        title="Configuration",
    ))

    asyncio.run(_run(model, prompt, editor_url, ws_url, verbose, clear))


async def _run(
    model_name: str,
    prompt: str,
    editor_url: str,
    ws_url: str,
    verbose: bool,
    clear: bool,
) -> None:
    # 1. Connect to editor
    client = EditorClient(ws_url)
    try:
        await client.connect()
        console.print("[green]Connected to editor[/green]")
    except Exception as e:
        console.print(f"[red]Failed to connect to editor at {ws_url}[/red]")
        console.print(f"[red]Make sure the relay server and editor are running.[/red]")
        console.print(f"[dim]Error: {e}[/dim]")
        sys.exit(1)

    set_client(client)

    # 2. Clear scene if requested
    if clear:
        await client.clear()
        console.print("[yellow]Scene cleared[/yellow]")

    # 3. Build the graph
    llm = get_model(model_name)
    app = compile_graph(llm)

    # 4. Run the pipeline
    initial_state = {
        "prompt": prompt,
        "model_name": model_name,
        "editor_url": editor_url,
        "ws_url": ws_url,
    }

    console.print("\n[bold]Starting pipeline...[/bold]\n")

    try:
        final_state = None
        async for event in app.astream(initial_state, stream_mode="updates"):
            for node_name, updates in event.items():
                if node_name == "architect":
                    spec = updates.get("architect_spec")
                    if spec:
                        console.print(f"[bold cyan]Architect Agent:[/bold cyan] Planning {spec.get('style', '')} building...")
                        console.print(f"  -> {spec.get('floors', '?')} floors, {sum(len(l.get('rooms', [])) for l in spec.get('levels', []))} rooms, {spec.get('roofType', '?')} roof")

                elif node_name == "floor_planner":
                    plans = updates.get("floor_plans", [])
                    if plans:
                        plan = plans[-1]
                        idx = plan.get("level_index", "?")
                        console.print(f"\n[bold yellow]Floor Planner [Floor {idx}]:[/bold yellow] Generating coordinates...")
                        console.print(f"  -> {len(plan.get('walls', []))} walls, {len(plan.get('slabs', []))} slabs, {len(plan.get('zones', []))} zones, {len(plan.get('windows', []))} windows, {len(plan.get('doors', []))} doors")

                elif node_name == "builder":
                    idx = updates.get("current_floor_index", 1) - 1
                    wall_map = updates.get("wall_id_map", {})
                    n_walls = len(wall_map.get(idx, []))
                    console.print(f"\n[bold green]Builder [Floor {idx}]:[/bold green] Constructing...")
                    console.print(f"  -> Created {n_walls} walls + slabs, ceilings, zones, doors, windows")

                elif node_name == "furnisher":
                    n_items = len(updates.get("built_node_ids", [])) - len(initial_state.get("built_node_ids", []))
                    console.print(f"\n[bold magenta]Furnisher:[/bold magenta] Placing furniture...")

                # Check for errors
                errors = updates.get("errors", [])
                for err in errors:
                    console.print(f"  [red]Error: {err}[/red]")

                final_state = updates

    except Exception as e:
        console.print(f"\n[red]Pipeline error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
    finally:
        await client.close()

    console.print(f"\n[bold green]Done! View your building at {editor_url}[/bold green]")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI shows help**

Run: `cd architectbot && python -m architect --help`
Expected: Shows usage with `--model`, `--prompt`, `--editor-url`, `--ws-url`, `--verbose`, `--clear` options

- [ ] **Step 3: Commit**

```bash
git add architect/__main__.py
git commit -m "feat: CLI entry point with rich output and streaming"
```

---

## Task 11: End-to-End Integration Test

**Files:**
- No new files. Manual integration test.

- [ ] **Step 1: Start the editor**

Terminal 1: `cd editor && bun dev`
Wait for `Ready in` message.

- [ ] **Step 2: Start the relay server**

Terminal 2: `cd editor/apps/editor && node bridge-relay.mjs`
Expected: `[Relay] WebSocket relay running on ws://localhost:3100`

- [ ] **Step 3: Open editor in browser**

Open `http://localhost:3002`
Expected in relay terminal: `[Relay] Editor connected`
Expected in browser console: `[Bridge] Connected to relay server`

- [ ] **Step 4: Set API key**

Set the appropriate environment variable for your chosen model:
```bash
export ANTHROPIC_API_KEY="sk-..."  # for Claude models
# or
export OPENAI_API_KEY="sk-..."  # for OpenAI models
```

- [ ] **Step 5: Run the architect**

Terminal 3:
```bash
cd architectbot
python -m architect --model claude-sonnet-4-6 --prompt "simple 1-story house with 2 bedrooms, kitchen, and living room" --clear --verbose
```

Expected: Pipeline runs through all 4 agents, building appears in editor.

- [ ] **Step 6: Verify in editor**

Check the editor at `http://localhost:3002`:
- Building should have walls forming rooms
- Floors (slabs) should be visible
- Zones should be colored by room type
- Doors should cut through walls
- Windows should cut through exterior walls

- [ ] **Step 7: Commit any fixes**

Fix any issues found during integration testing and commit.

---

## Summary

| Task | Component | Key Files |
|------|-----------|-----------|
| 1 | Bridge Types + Handler | `command-handler.ts`, `types.ts` |
| 2 | BridgeProvider | `bridge-provider.tsx`, `page.tsx` |
| 3 | WebSocket Relay | `bridge-relay.mjs` |
| 4 | Python Package | `pyproject.toml`, `state.py`, `config.py` |
| 5 | WebSocket Client | `client.py` |
| 6 | LangChain Tools | `tools/editor.py` |
| 7 | Agent Prompts | `prompts/*.md` |
| 8 | Agent Implementations | `agents/*.py` |
| 9 | LangGraph Pipeline | `graph.py` |
| 10 | CLI Entry Point | `__main__.py` |
| 11 | Integration Test | Manual E2E test |
