# AI Architect System — Design Spec

## Overview

A CLI-driven, multi-agent system that generates complete 3D buildings in the Pascal Editor from natural language prompts. The user provides a prompt and LLM model choice; a LangChain/LangGraph pipeline plans the building floor-by-floor and executes it via WebSocket commands to the live editor.

```
python architect.py --model claude-sonnet-4-6 --prompt "3-bedroom modern house, 2 floors"
-> Building appears live at http://localhost:3002
```

## Architecture

```
User (CLI)
    |
    v
Python LangGraph Pipeline (sequential)
    |
    |-- 1. Architect Agent --- plans structure (pure reasoning, no API)
    |
    |-- 2. Floor Planner Agent --+
    |                            +-- loops per floor
    |-- 3. Builder Agent --------+
    |
    |-- 4. Furnisher Agent --- places furniture in all rooms
    |
    v
Pascal Editor (browser, http://localhost:3002)
    <-- controlled via WebSocket bridge to browser-side Zustand stores
```

## Component 1: WebSocket Bridge (Editor <-> Python)

### Why Not REST API Routes?

Zustand stores (`useScene`, `useViewer`, `useEditor`) are client-side only (marked `'use client'`). Next.js API routes run on the server and would create separate, empty store instances with no connection to the browser. A WebSocket bridge solves this: the Python client sends commands over WebSocket, the browser tab receives them and executes on the real Zustand stores, then returns results.

### Bridge Architecture

```
Python (WebSocket client)          Browser (WebSocket handler)
    |                                   |
    |-- {"cmd": "read_state"} -------->|
    |                                   |-- useScene.getState()
    |<-- {"nodes": {...}, ...} --------|
    |                                   |
    |-- {"cmd": "create_node",  ------>|
    |    "node": {...},                 |-- useScene.getState().createNode(...)
    |    "parentId": "..."}             |
    |<-- {"id": "wall_abc", ok: true} -|
```

### WebSocket Server

A lightweight WebSocket server runs inside the Next.js app (or as a standalone script injected into the page). The browser tab connects on load.

**Implementation:** Add a `BridgeProvider` React component at the app root that:

1. Opens a WebSocket server on `ws://localhost:3100`
2. Listens for incoming JSON commands
3. Dispatches to the appropriate Zustand store action
4. Returns the result as JSON

### Command Protocol

Every command is a JSON message with a `cmd` field and a unique `id` for request/response correlation.

#### State Reading

| Command                                     | Returns                                                             |
| ------------------------------------------- | ------------------------------------------------------------------- |
| `{"cmd": "read_state"}`                     | Full scene: all nodes, root IDs, selection, viewer/editor settings  |
| `{"cmd": "read_nodes"}`                     | All nodes as flat dict                                              |
| `{"cmd": "read_nodes", "type": "wall"}`     | Filter nodes by type                                                |
| `{"cmd": "read_node", "nodeId": "..."}`     | Single node with all properties                                     |
| `{"cmd": "read_viewer"}`                    | Camera mode, theme, unit, level mode, wall mode, visibility toggles |
| `{"cmd": "read_editor"}`                    | Phase, mode, active tool, structure layer                           |
| `{"cmd": "read_assets", "category": "..."}` | Available furniture/fixture assets from catalog                     |

#### Node CRUD

| Command                                                                | Description                                                    |
| ---------------------------------------------------------------------- | -------------------------------------------------------------- |
| `{"cmd": "create_node", "node": {...}, "parentId": "..."}`             | Create node (any type), returns created node with generated ID |
| `{"cmd": "create_nodes", "ops": [{"node": {...}, "parentId": "..."}]}` | Batch create                                                   |
| `{"cmd": "update_node", "nodeId": "...", "data": {...}}`               | Partial update any node property                               |
| `{"cmd": "update_nodes", "updates": [{"id": "...", "data": {...}}]}`   | Batch update                                                   |
| `{"cmd": "delete_node", "nodeId": "..."}`                              | Delete node + children recursively                             |
| `{"cmd": "delete_nodes", "ids": ["..."]}`                              | Batch delete                                                   |

**ID Generation:** The browser-side handler runs node data through the appropriate Zod schema's `.parse()` method, which auto-generates IDs in the correct `{type}_{nanoid}` format. The Python client does NOT need to generate IDs.

#### Viewer/Editor Control

| Command                                                                                                               | Description                                                                         |
| --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `{"cmd": "set_selection", "buildingId?": "...", "levelId?": "...", "zoneId?": "...", "selectedIds?": [...]}`          | Set selection. Note: changing a parent resets child selections (hierarchy cascade). |
| `{"cmd": "set_camera", "cameraMode?": "...", "levelMode?": "...", "wallMode?": "..."}`                                | Camera/display mode                                                                 |
| `{"cmd": "set_display", "showScans?": bool, "showGuides?": bool, "showGrid?": bool, "theme?": "...", "unit?": "..."}` | Display settings                                                                    |
| `{"cmd": "set_tool", "tool?": "...", "phase?": "...", "mode?": "..."}`                                                | Active tool/phase/mode                                                              |

#### Actions

| Command             | Description                                                           |
| ------------------- | --------------------------------------------------------------------- |
| `{"cmd": "undo"}`   | Undo last action                                                      |
| `{"cmd": "redo"}`   | Redo                                                                  |
| `{"cmd": "clear"}`  | Clear scene (note: reloads default Site > Building > Level hierarchy) |
| `{"cmd": "export"}` | Export scene data as JSON                                             |

#### Collections

| Command                                                                     | Description       |
| --------------------------------------------------------------------------- | ----------------- |
| `{"cmd": "create_collection", "name": "...", "nodeIds?": [...]}`            | Create collection |
| `{"cmd": "update_collection", "collectionId": "...", "data": {...}}`        | Update name/color |
| `{"cmd": "delete_collection", "collectionId": "..."}`                       | Delete collection |
| `{"cmd": "add_to_collection", "collectionId": "...", "nodeId": "..."}`      | Add node          |
| `{"cmd": "remove_from_collection", "collectionId": "...", "nodeId": "..."}` | Remove node       |

### Supported Node Types and Their Full Parameters

**SiteNode:**

- `polygon?: {type: 'polygon', points: [number, number][]}`

**BuildingNode:**

- `position: [x, y, z]`
- `rotation: [x, y, z]`

**LevelNode:**

- `level: number` (floor index, 1 = ground, 0 = basement)

**WallNode:**

- `start: [x, z]` -- start point on 2D floor plan
- `end: [x, z]` -- end point on 2D floor plan
- `thickness?: number` (default 0.1m)
- `height?: number` (default 2.5m)
- `frontSide: 'interior' | 'exterior' | 'unknown'`
- `backSide: 'interior' | 'exterior' | 'unknown'`

**SlabNode:**

- `polygon: [x, z][]` -- floor outline
- `holes?: [x, z][][]` -- cutouts (e.g., stairwell)
- `elevation: number` (default 0.05m)

**CeilingNode:**

- `polygon: [x, z][]` -- ceiling outline
- `holes?: [x, z][][]`
- `height: number` (default 2.5m)

**ZoneNode:**

- `name: string`
- `polygon: [x, z][]`
- `color: string` (hex, e.g., '#3b82f6')

**RoofNode** (container -- parent of RoofSegmentNodes):

- `position: [x, y, z]`
- `rotation: number` (radians)

**RoofSegmentNode** (child of RoofNode -- holds actual geometry):

- `roofType: 'hip' | 'gable' | 'shed' | 'gambrel' | 'dutch' | 'mansard' | 'flat'`
- `position: [x, y, z]`
- `rotation: number`
- `width: number` (default 8)
- `depth: number` (default 6)
- `wallHeight: number` (default 0.5)
- `roofHeight: number` (default 2.5)
- `wallThickness: number` (default 0.1)
- `deckThickness: number` (default 0.1)
- `overhang: number` (default 0.3)
- `shingleThickness: number` (default 0.05)

**ItemNode (furniture/fixtures):**

- `position: [x, y, z]`
- `rotation: [x, y, z]`
- `scale: [x, y, z]`
- `asset: {id, category, name, thumbnail, src, dimensions, attachTo?, offset, rotation, scale, surface?, interactive?}`
- `wallId?: string` -- if attached to wall
- `wallT?: number` -- 0-1 parametric position on wall (ItemNode only, NOT windows/doors)
- `side?: 'front' | 'back'`

**WindowNode** (must be child of a WallNode -- parentId = wallId):

- `position: [x, y, z]` -- wall-local coordinates where x = distance along wall from center, y = height of window center
- `rotation: [x, y, z]`
- `wallId: string` -- the wall this window is on (MUST match parentId)
- `side: 'front' | 'back'`
- `width: number` (default 1.5)
- `height: number` (default 1.5)
- `frameThickness: number` (default 0.05)
- `frameDepth: number` (default 0.07)
- `columnRatios: number[]` (default [1])
- `rowRatios: number[]` (default [1])
- `columnDividerThickness: number` (default 0.03)
- `rowDividerThickness: number` (default 0.03)
- `sill: boolean` (default true)
- `sillDepth: number` (default 0.08)
- `sillThickness: number` (default 0.03)

**DoorNode** (must be child of a WallNode -- parentId = wallId):

- `position: [x, y, z]` -- wall-local coordinates where x = distance along wall from center, y = height of door center
- `rotation: [x, y, z]`
- `wallId: string` -- the wall this door is on (MUST match parentId)
- `side: 'front' | 'back'`
- `width: number` (default 0.9)
- `height: number` (default 2.1)
- `frameThickness: number` (default 0.05)
- `frameDepth: number` (default 0.07)
- `threshold: boolean` (default true)
- `thresholdHeight: number` (default 0.02)
- `hingesSide: 'left' | 'right'` (default 'left')
- `swingDirection: 'inward' | 'outward'` (default 'inward')
- `segments: {type: 'panel'|'glass'|'empty', heightRatio, columnRatios?, dividerThickness?, panelDepth?, panelInset?}[]`
- `handle: boolean` (default true)
- `handleHeight: number` (default 1.05)
- `handleSide: 'left' | 'right'` (default 'right')
- `contentPadding: [number, number]` (default [0.04, 0.04])
- `doorCloser: boolean` (default false)
- `panicBar: boolean` (default false)
- `panicBarHeight: number` (default 1.0)

**ScanNode:**

- `url: string`
- `position: [x, y, z]`
- `rotation: [x, y, z]`
- `scale: number`
- `opacity: number` (0-100)

**GuideNode:**

- `url: string`
- `position: [x, y, z]`
- `rotation: [x, y, z]`
- `scale: number`
- `opacity: number` (0-100)

### Node Hierarchy Rules

```
Site
  +-- Building (parentId = siteId)
       +-- Level (parentId = buildingId)
            +-- Wall (parentId = levelId)
            |    +-- Window (parentId = wallId, NOT levelId)
            |    +-- Door (parentId = wallId, NOT levelId)
            |    +-- Item (parentId = wallId, if wall-mounted)
            +-- Slab (parentId = levelId)
            +-- Ceiling (parentId = levelId)
            |    +-- Item (parentId = ceilingId, if ceiling-mounted)
            +-- Zone (parentId = levelId)
            +-- Roof (parentId = levelId)
            |    +-- RoofSegment (parentId = roofId)
            +-- Item (parentId = levelId, if floor-standing)
            +-- Scan (parentId = levelId)
            +-- Guide (parentId = levelId)
```

**Critical: Windows and doors MUST have parentId set to the wall ID.** This is required for the CSG cutout geometry system to work. Setting parentId to the level ID will silently break wall rendering.

## Component 2: LangGraph Agent Pipeline

### Shared State

```python
class BuildState(TypedDict):
    prompt: str
    model_name: str
    editor_url: str                    # http://localhost:3002
    ws_url: str                        # ws://localhost:3100
    architect_spec: dict | None        # output of Architect
    current_floor_index: int           # tracks loop position
    total_floors: int
    floor_plans: list[dict]            # output of Floor Planner (accumulated)
    built_node_ids: list[str]          # output of Builder (accumulated)
    building_id: str | None            # reuse default or created building node ID
    level_ids: list[str]               # created level node IDs
    wall_id_map: dict[str, list[str]]  # per-floor: wall_index -> wall_id mapping
    errors: list[str]                  # any errors encountered
```

### Graph Definition

```python
graph = StateGraph(BuildState)

graph.add_node("architect", architect_agent)
graph.add_node("floor_planner", floor_planner_agent)
graph.add_node("builder", builder_agent)
graph.add_node("furnisher", furnisher_agent)

graph.set_entry_point("architect")
graph.add_edge("architect", "floor_planner")
graph.add_edge("floor_planner", "builder")

def check_floors_remaining(state: BuildState) -> str:
    if state["current_floor_index"] < state["total_floors"] - 1:
        return "more_floors"
    return "done"

graph.add_conditional_edges("builder", check_floors_remaining, {
    "more_floors": "floor_planner",
    "done": "furnisher",
})
graph.add_edge("furnisher", END)
```

### Agent 1: Architect Agent

**Role:** Pure reasoning. Takes the user prompt, outputs a structured building spec.

**System prompt context:** Building design knowledge -- room size standards, circulation patterns, structural constraints.

**Input:** `state.prompt`

**Output:** `state.architect_spec` -- JSON with:

- `style` (modern, traditional, etc.)
- `floors` count
- `levels[]` each with `rooms[]` containing:
  - `type`: room type (living, kitchen, bedroom, bathroom, hallway, office, garage, etc.)
  - `approxArea`: target area in square meters
  - `position`: rough `[x, z]` centroid hint in meters from origin (e.g., `[2.5, 3.0]`)
- `roofType`
- `exteriorWallHeight`
- `buildingFootprint`: `[width, depth]` in meters

**Tools:** None (pure LLM reasoning)

**Validation:** Must produce valid JSON matching expected schema. Retry up to 2 times on failure.

### Agent 2: Floor Planner Agent

**Role:** Converts one floor from the architect spec into exact 2D coordinates.

**Input:** `state.architect_spec.levels[current_floor_index]`

**Output:** Appends to `state.floor_plans[]`:

```json
{
  "level_index": 0,
  "walls": [
    {"start": [0, 0], "end": [10, 0], "thickness": 0.2, "height": 2.8}
  ],
  "slabs": [
    {"polygon": [[0, 0], [10, 0], [10, 8], [0, 8]], "elevation": 0.05}
  ],
  "ceilings": [
    {"polygon": [[0, 0], [10, 0], [10, 8], [0, 8]], "height": 2.5}
  ],
  "zones": [
    {"name": "Living Room", "polygon": [[0, 0], [5, 0], [5, 4], [0, 4]], "color": "#3b82f6"}
  ],
  "doors": [
    {"wall_index": 3, "position_along_wall": 2.5, "width": 0.9, "height": 2.1, "side": "front"}
  ],
  "windows": [
    {"wall_index": 0, "position_along_wall": 3.0, "width": 1.5, "height": 1.5, "side": "front"}
  ],
  "roofs": [
    {"roof_type": "gable", "width": 10, "depth": 8, "roof_height": 2.5, "wall_height": 0.5}
  ]
}
```

**Tools:**

- `read_state()` -- reads current editor state to avoid conflicts with already-built floors

**Constraints:**

- All coordinates in meters, aligned to 0.5m grid
- Walls must form closed loops for exterior
- Interior walls connect to exterior walls
- `position_along_wall` is distance in meters from wall start (NOT parametric 0-1)
- Room polygons must not overlap
- Roofs only on top floor

### Agent 3: Builder Agent

**Role:** Executes the floor plan by calling WebSocket commands. Creates actual nodes.

**Input:** `state.floor_plans[current_floor_index]`

**Output:**

- Appends created node IDs to `state.built_node_ids[]`
- Appends wall ID mapping to `state.wall_id_map[floor_index]`
- **Increments `state.current_floor_index` by 1**

**Tools (LangChain @tool functions, each sends WebSocket command):**

- `read_state() -> dict` -- read current scene to find existing building/level IDs
- `create_level(building_id, level_number) -> level_id`
- `create_wall(level_id, start, end, thickness, height) -> wall_id`
- `create_slab(level_id, polygon, elevation) -> slab_id`
- `create_ceiling(level_id, polygon, height) -> ceiling_id`
- `create_zone(level_id, name, polygon, color) -> zone_id`
- `create_door(wall_id, position_along_wall, width, height, side, hinges_side, swing_direction) -> door_id`
  - Creates DoorNode with `parentId = wall_id`, converts `position_along_wall` to wall-local position
- `create_window(wall_id, position_along_wall, width, height, side) -> window_id`
  - Creates WindowNode with `parentId = wall_id`, converts `position_along_wall` to wall-local position
- `create_roof(level_id, roof_type, width, depth, roof_height, wall_height) -> roof_segment_id`
  - Internally creates both RoofNode (child of level) and RoofSegmentNode (child of roof)
- `select_level(level_id)` -- focus editor on current floor
- `undo()` -- rollback on failure

**Execution order for each floor:**

1. Read state to find existing building ID (reuse default from `loadScene()`)
2. Create level (reuse existing level-0 if first floor)
3. Create slab
4. Create exterior walls (store ordered `wall_ids[]` array)
5. Create interior walls (append to `wall_ids[]`)
6. Create doors on walls (lookup `wall_ids[wall_index]` from floor plan)
7. Create windows on walls (same lookup)
8. Create ceiling
9. Create zones
10. Create roof (only on top floor) -- creates RoofNode + RoofSegmentNode
11. Read state to verify all nodes exist
12. Increment `current_floor_index`

**Error handling:** If an API call fails mid-floor, call `undo()` repeatedly to rollback partial work, log error, and continue to next floor.

**Default scene handling:** When the editor starts, `loadScene()` auto-creates a default Site > Building > Level(0) hierarchy. The Builder MUST:

- On first floor: read state to find the existing building ID and level-0 ID, reuse them
- On subsequent floors: create new Level nodes under the existing building

### Agent 4: Furnisher Agent

**Role:** Places furniture in every room based on room type.

**Input:** `state.built_node_ids`, reads zones from editor state

**Output:** Item node IDs added to `state.built_node_ids`

**Tools:**

- `read_zones() -> list[zone]` -- get all zones with names and polygons
- `read_available_assets(category) -> list[asset]` -- query catalog via `read_assets` command
- `create_item(level_id, asset, position, rotation) -> item_id`
  - Floor-standing items: `parentId = levelId`
  - Wall-mounted items: `parentId = wallId`
  - Ceiling-mounted items: `parentId = ceilingId`
- `read_state() -> dict` -- verify placements

**Room-type furniture mapping (built into system prompt):**

- bedroom: bed, nightstand(s), wardrobe
- living: sofa, coffee table, TV unit, armchair
- kitchen: dining table, chairs, island/counter
- bathroom: (fixtures from catalog)
- hallway: console table, coat rack
- office: desk, chair, bookshelf

**Placement logic:** Items placed within zone polygon bounds, with clearance from walls (min 0.3m from wall surfaces).

## Component 3: CLI Entry Point

### Installation

```bash
cd architectbot
pip install -e .
```

### Usage

```bash
# Basic
python -m architect --model claude-sonnet-4-6 --prompt "3-bedroom modern house"

# All options
python -m architect \
  --model claude-sonnet-4-6 \
  --prompt "2-story villa, 4 bedrooms, open kitchen, garage" \
  --editor-url http://localhost:3002 \
  --ws-url ws://localhost:3100 \
  --verbose \
  --clear  # clear existing scene first
```

### Supported Models

Any model supported by LangChain:

- `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-haiku-4-5` (Anthropic)
- `gpt-4o`, `gpt-4.1` (OpenAI)
- Others via LangChain model registry

### Terminal Output

```
Architect Agent: Planning 2-story modern house...
  -> 2 floors, 7 rooms, gable roof

Floor Planner [Floor 0 - Ground]: Generating coordinates...
  -> 12 walls, 1 slab, 4 zones, 3 windows, 2 doors

Builder [Floor 0 - Ground]: Constructing...
  -> Reusing existing building_abc and level_0_def
  -> Created: 12 walls, 1 slab, 4 zones, 3 windows, 2 doors

Floor Planner [Floor 1 - First]: Generating coordinates...
  -> 10 walls, 1 slab, 3 zones, 4 windows, 1 door

Builder [Floor 1 - First]: Constructing...
  -> Created: level, 10 walls, 1 slab, 3 zones, 4 windows, 1 door, 1 roof

Furnisher: Placing furniture in 7 rooms...
  -> Living Room: sofa, coffee table, TV unit
  -> Kitchen: dining table, 4 chairs
  -> 3x Bedroom: bed, nightstand, wardrobe
  -> Bathroom: (fixtures placed)

Done! View at http://localhost:3002
```

## Project Structure

```
architectbot/
|-- pyproject.toml              # Python package config
|-- architect/
|   |-- __init__.py
|   |-- __main__.py             # CLI entry point (click)
|   |-- config.py               # Model registry, defaults
|   |-- graph.py                # LangGraph state machine definition
|   |-- state.py                # BuildState TypedDict
|   |-- client.py               # WebSocket client for editor communication
|   |-- agents/
|   |   |-- __init__.py
|   |   |-- architect.py        # Architect agent (planning)
|   |   |-- floor_planner.py    # Floor planner agent (coordinates)
|   |   |-- builder.py          # Builder agent (API execution)
|   |   +-- furnisher.py        # Furnisher agent (furniture)
|   |-- tools/
|   |   |-- __init__.py
|   |   +-- editor.py           # LangChain @tool wrappers for WebSocket commands
|   +-- prompts/
|       |-- architect.md        # System prompt for Architect agent
|       |-- floor_planner.md    # System prompt for Floor Planner
|       |-- builder.md          # System prompt for Builder
|       +-- furnisher.md        # System prompt for Furnisher
```

## Editor-Side Changes

A single `BridgeProvider` component added to the editor app root. No new API routes needed.

```
apps/editor/
|-- components/
|   +-- bridge/
|       |-- bridge-provider.tsx    # WebSocket server + command dispatcher
|       +-- command-handler.ts     # Maps commands to Zustand store actions
```

### BridgeProvider

React component mounted at app root. On mount:

1. Starts WebSocket server on `ws://localhost:3100`
2. Accepts connections from Python client
3. Parses incoming JSON commands
4. Dispatches to appropriate store (`useScene`, `useViewer`, `useEditor`)
5. Returns results as JSON

### Command Handler

Maps command strings to store actions:

```typescript
// command-handler.ts
import { useScene } from '@pascal-app/core'
import { useViewer } from '@pascal-app/viewer'
import { useEditor } from '@/store/use-editor'
import { CATALOG_ITEMS } from '@/components/ui/item-catalog/catalog-items'

export function handleCommand(cmd: any): any {
  switch (cmd.cmd) {
    case 'read_state':
      return {
        nodes: useScene.getState().nodes,
        rootNodeIds: useScene.getState().rootNodeIds,
        viewer: useViewer.getState(),
        editor: useEditor.getState(),
      }
    case 'create_node':
      // Parse through Zod schema to auto-generate ID
      useScene.getState().createNode(cmd.node, cmd.parentId)
      return { id: cmd.node.id, ok: true }
    case 'read_assets':
      return CATALOG_ITEMS.filter(i => !cmd.category || i.category === cmd.category)
    // ... all other commands
  }
}
```

**Note on LevelNode children:** The LevelNode Zod schema does not include ItemNode in its children union. The existing editor works around this with `as any`. The command handler should follow the same pattern for furniture placement.

## Dependencies

### Python (architectbot)

- `langchain-core` -- base abstractions
- `langgraph` -- state machine orchestration
- `langchain-anthropic` -- Claude models
- `langchain-openai` -- OpenAI models
- `websockets` -- WebSocket client
- `click` -- CLI framework
- `rich` -- terminal output formatting

### Editor (bridge only)

- `ws` or built-in WebSocket -- for WebSocket server in browser context
- No other new dependencies. Bridge uses existing Zustand stores and catalog data.

## Key Constraints

1. **Sequential pipeline** -- Each agent depends on the previous. No parallel execution.
2. **Per-floor loop** -- Floor Planner + Builder loop for each floor. Builder increments `current_floor_index`.
3. **State verification** -- Builder reads editor state after each floor to confirm nodes were created.
4. **Coordinate system** -- Editor uses meters. X = east, Y = up, Z = south. Floor plans are 2D (X, Z).
5. **Wall grid** -- Walls snap to 0.5m grid. Agents should output coordinates aligned to 0.5m.
6. **Node hierarchy** -- Site > Building > Level > (Walls, Slabs, Zones, etc.). ParentId must be set correctly.
7. **Windows/doors are wall children** -- parentId MUST be the wall ID for CSG cutouts to work.
8. **Roofs are two nodes** -- RoofNode (container, child of level) + RoofSegmentNode (geometry, child of roof).
9. **Default scene** -- Editor auto-creates Site > Building > Level(0). Builder reuses these, does not create duplicates.
10. **Editor must be running** -- Browser must have `localhost:3002` open. WebSocket bridge runs client-side.
11. **ID generation** -- Browser-side Zod schemas generate node IDs. Python client does not generate IDs.
