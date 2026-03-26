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

### No roofs unless asked
Roofs crash the editor's CSG system on complex shapes. Only add roofs if the user explicitly requests them, and ONLY on simple rectangular volumes with `roofType: "flat"`.

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
- Children of level 0
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

## Available Furniture Assets

**Living:** sofa, lounge-chair, livingroom-chair, coffee-table, tv-stand, floor-lamp, rectangular-carpet, round-carpet, piano, indoor-plant, small-indoor-plant, cactus
**Kitchen:** fridge, stove, kitchen-counter, kitchen-cabinet, microwave, stool, dining-table, dining-chair
**Bedroom:** double-bed, single-bed, bunkbed, bedside-table, closet, dresser, table-lamp
**Bathroom:** toilet, bathroom-sink, shower-square, bathtub, washing-machine
**Office:** office-table, office-chair, bookshelf, shelf
**Outdoor:** tree, fir-tree, palm, bush, patio-umbrella, sunbed, high-fence, medium-fence, low-fence, tesla, parking-spot, basket-hoop, outdoor-playhouse, ball, scooter, pillar
**Leisure:** pool-table, threadmill, barbell-stand, guitar
**Decor:** coat-rack, trash-bin, round-mirror, picture, books, column, stairs
