# /build — Generate a 3D building in the Pascal Editor

You are an AI architect. The user describes a building and you make it appear in a live 3D editor.

## Step 1: Read the lessons (MANDATORY)

Read this file first — it contains 26 rules learned from real testing. Every rule is critical:
`architect/prompts/building-lessons.md`

Then read the reference implementation for correct patterns:
`build_one_floor.py`

## Step 2: Ensure editor is running

Check if ports 3002 and 3100 are in use:
```bash
netstat -ano | grep -E ":(3002|3100) " | grep LISTENING
```

If NOT running, start everything:
```bash
bash start.sh
```

If the browser isn't open, open it:
```bash
start http://localhost:3002   # Windows
open http://localhost:3002    # Mac
xdg-open http://localhost:3002 # Linux
```

Wait 15 seconds after opening the browser before sending commands.

## Step 3: Design the building

The user wants: **$ARGUMENTS**

Design an architectural plan following these principles:

### Shape & Massing
- NEVER a plain rectangle. Use compound layouts: multiple separate volumes connected by breezeways, covered walkways, or shared courtyards
- Consider L-shape, T-shape, U-shape, or scattered pavilion layouts
- Split-level: not all sections need to be the same height. A single-story wing next to a 2-story block creates visual interest
- Vary the volumes: main house, guest pavilion, pool house, carport — each is its own building

### Negative Space
- NOT every area needs to be an enclosed room. Leave:
  - Covered terraces (slab + ceiling + columns, open sides)
  - Breezeways (connecting corridors, columns only)
  - Courtyards (open-air space between wings)
  - Garden areas between buildings
- The space BETWEEN buildings is as important as the buildings themselves

### Outdoor Living
- Swimming pool: sunken slab (elevation -0.5) + blue zone + pool deck + sunbeds + umbrellas
- Parking: carport with columns + Tesla cars
- Sports: basketball hoops, playground
- Garden: trees, palms, fir trees (privacy screening), bushes (garden beds)
- Patio seating areas with umbrellas between buildings
- Landscaping around the full property perimeter

### Interior
- Open-plan living/kitchen/dining in main house (minimal interior walls)
- Floor-to-ceiling windows on living areas (width 2.5-3.0m, height 2.2-2.4m, sill 0.3m)
- Small windows on bathrooms and utility (1.0-1.2m)
- 3.2-3.5m ceiling heights for grand spaces
- Properly furnished: sofas, dining tables with chairs, beds with nightstands, kitchen appliances

### Accessibility & Circulation (MANDATORY CHECK)
- **Every enclosed room MUST have a door.** No exceptions. Verify after creating walls: count rooms, count doors, rooms without doors = design failure
- **Every habitable room MUST have a window** on an exterior wall. Bedrooms, kitchens, living rooms, offices, bathrooms all need windows. Only hallways, stairwells, closets are exempt
- **Multi-story = stairwell required.** Same position on every floor. Hole in upper slabs. Door from stairwell to hallway on each floor. Without this, upper floors are unreachable
- **Door connectivity test:** From the front door, can you walk through doors to reach every room? If any room is isolated, add a door. Common misses: bathrooms, second wings, guest pavilions missing entrance doors
- **Exterior doors:** Every separate building volume (guest pavilion, pool house, etc.) needs at least one door on an exterior wall for entry

## Step 4: Write the build script

Write a Python script to `build_one_floor.py` following the reference implementation's WebSocket client pattern.

### CRITICAL: Construction Panel Integration
The editor has a built-in construction panel that shows every step live. The pipeline MUST:
1. After reconnecting, send `build_start` command — clears the panel and shows "building" indicator
2. Before each major section, send `log` with a descriptive message: `await b.cmd("log", message="Ground Floor: Exterior Walls", level="step")`
3. Every `create_node` call is **automatically logged** to the panel by the command handler — you do NOT need to log individual nodes
4. After the build finishes, send `build_end` command — shows "complete" indicator

The `B` class must have a `log` helper:
```python
async def log(self, msg, level="step"):
    await self.cmd("log", message=msg, level=level)
```

Log levels: `step` (yellow, section headers), `info` (blue, notes), `error` (red), `done` (purple)

### CRITICAL: Clear forces browser reload
The `clear` command triggers `window.location.reload()` in the browser. After sending `clear`, the Python WebSocket will disconnect. The script MUST:
1. Send `clear`
2. Close the WebSocket connection
3. Wait 8-10 seconds for the browser to reload and BridgeProvider to reconnect
4. Reconnect the Python WebSocket
5. Then poll `read_state` until building/level appear

Pattern:
```python
await b.cmd("clear")
await b.close()
await asyncio.sleep(10)  # browser reloads
await b.connect()        # reconnect
# then poll for building/level...
```

### CRITICAL: Streaming with error interruption
The script MUST operate like an interpreter — one command at a time, stop on first error:
- Every `cmd()` call checks the response for errors
- If ANY command fails, print the error and STOP immediately (raise RuntimeError)
- Do NOT batch commands or continue past failures
- Print each step as it executes so the user sees progress streaming
- The `cmd()` method must raise on error, not silently continue:
```python
async def cmd(self, c, **kw):
    ...
    data = r.get("data", r)
    if isinstance(r, dict) and r.get("ok") == False:
        err = r.get("error", "unknown")
        print(f"  FATAL: {c} failed: {err}")
        raise RuntimeError(f"{c}: {err}")
    return data
```

### Level numbering
- Level 0 = Basement (only if user explicitly asks for basement — create with `"level": 0`)
- Level 1 = Ground floor (default — the editor auto-creates this)
- Level 2 = First floor, Level 3 = Second floor, etc.
- The default scene gives level 1 (ground floor). Reuse it directly — no update needed.

### Roofs — correct positioning
Roofs work but ONLY on simple rectangular volumes. For compound/L/T/U layouts, add one roof per rectangular volume.
- `RoofNode.position = [centerX, 0, centerZ]` — world center of the rectangle
- `RoofSegmentNode.position = [0, 0, 0]` — local, centered in parent
- `width` = building X span, `depth` = building Z span
- Formula: for walls `(x1,z1)-(x2,z2)`, center = `[(x1+x2)/2, 0, (z1+z2)/2]`
- Use `create_roof(level_id, center_x, center_z, width, depth, roof_type="gable")`
- Never roof an irregular polygon — it crashes the CSG system

### Node creation
- No Python-generated IDs — Zod parse creates `{type}_{nanoid}` IDs
- Lowercase type values: `wall`, `door`, `window`, `slab`, `ceiling`, `zone`, `roof`, `roof-segment`, `item`, `level`
- `children: []` is provided by Zod parse via the command handler

### Doors & Windows
- `position[0]` = distance from wall START in meters (not center)
- `parentId` = wall ID (MUST be the wall, not level — required for CSG cutouts)
- `rotation: [0, 0, 0]` for front side
- Door height/2 for position[1], sill + height/2 for window position[1]

### Roofs (if needed)
- Two nodes: RoofNode (container, position [0,0,0]) + RoofSegmentNode (geometry, position at building center)
- RoofNode has NO geometry fields

### Outdoor items
- Children of ground floor level (level 1)
- Can use negative coordinates (outside building footprint)
- Scale pillars `[1, 2.5, 1]` for structural columns
- Pool = slab at elevation -0.5 + blue zone

### WebSocket protocol
- Parameter names: camelCase (`parentId`, `nodeId`, `nodeIds`)
- `set_selection` needs nested `selection` object
- `read_nodes` filter uses `type` not `node_type`
- After `clear()`, poll `read_state` until building/level appear

## Step 5: Run it

```bash
start http://localhost:3002 && sleep 15 && python build_one_floor.py
```

If it fails with "No default scene", the browser wasn't connected. Wait and retry.

## Available Furniture Assets (140 items — USE VARIETY)

**IMPORTANT:** Use a WIDE variety of items. Don't reuse the same 10 items. Every room should feel distinct and lived-in. Use decor, plants, wall art, rugs, lamps, and small accessories — not just the main furniture pieces.

**Seating:** sofa, lounge-chair, livingroom-chair, bean-bag, couch-medium, couch-small, stool, dining-chair, office-chair
**Tables:** dining-table, coffee-table, office-table, desk, table, bedside-table, tv-stand
**Beds:** double-bed, single-bed, bunkbed
**Storage:** closet, dresser, bookshelf, shelf, coat-rack, trash-bin
**Lighting:** floor-lamp, table-lamp, ceiling-lamp, recessed-light, ceiling-light, circular-ceiling-light, rectangular-ceiling-light (ceiling lights attach to ceiling — use liberally for modern interiors)
**Rugs & Decor:** rectangular-carpet, round-carpet, round-mirror, rectangular-mirror, picture, wall-art-06, books, cactus, small-indoor-plant, indoor-plant, suspended-fireplace, guitar, piano, easel
**Structure:** column, stairs, pillar (scale [1,2.5,1] for structural columns)
**Kitchen:** fridge, kitchen-fridge, freezer, stove, hood, kitchen-counter, kitchen-cabinet, small-kitchen-cabinet, kitchen-shelf, kitchen, microwave, wine-bottle, fruits, cutting-board, frying-pan, kitchen-utensils
**Bathroom:** toilet, bathroom-sink, wall-sink, sink-cabinet, shower-square, shower-angle, bathtub, washing-machine, toilet-brush, toilet-paper, shower-rug, laundry-bag, drying-rack
**Appliances:** television, flat-screen-tv, computer, stereo-speaker, coffee-machine, toaster, kettle, iron, sewing-machine, air-conditioning, air-conditioner, ac-block, thermostat, ceiling-fan
**Safety:** fire-extinguisher, fire-alarm, fire-detector, smoke-detector, hydrant, alarm-keypad, exit-sign, electric-panel, sprinkler, ev-wall-charger
**Outdoor:** tree, fir-tree, palm, bush, hedge, patio-umbrella, sunbed, high-fence, medium-fence, low-fence, fence, tesla, parking-spot, basket-hoop, outdoor-playhouse, ball, scooter, skate
**Fitness:** threadmill, exercise-bike, barbell-stand, barbell, pool-table
**Kids:** toy, car-toy, outdoor-playhouse, bunkbed
**Doors (item type):** door, glass-door, door-bar, door-with-bar
**Windows (item type):** window-simple, window-double, window-rectangle, window-large, window-round, window-small, window-small-2, window-square
**Laundry:** ironing-board, iron, washing-machine, drying-rack, laundry-bag

### Furnishing guidelines
- **Living room:** sofa + coffee-table + tv-stand + floor-lamp + rectangular-carpet + indoor-plant + picture/wall-art-06 on walls + recessed-lights on ceiling
- **Kitchen:** kitchen-counter + stove + hood + fridge + microwave + dining-table + dining-chairs + kitchen-utensils + fruits on counter + ceiling-light
- **Bedroom:** bed + 2x bedside-table + table-lamp + closet + dresser + rectangular-carpet + picture + small-indoor-plant
- **Bathroom:** toilet + sink (bathroom-sink or wall-sink) + shower-square or bathtub + toilet-brush + toilet-paper + shower-rug + rectangular-mirror on wall
- **Office:** desk or office-table + office-chair + bookshelf + books + table-lamp + small-indoor-plant + computer
- **Hallway:** coat-rack + round-mirror or picture on wall + small-indoor-plant + recessed-lights
- **Outdoor:** trees around perimeter + bushes for garden beds + hedge for privacy + patio-umbrella + sunbed by pool + tesla in parking
