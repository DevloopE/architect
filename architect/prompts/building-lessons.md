# Building Lessons — Learned from Real Editor Testing

These are hard-won lessons from building in the Pascal Editor. Every agent MUST follow these rules.

## Execution Rules (MOST IMPORTANT)

0. **Stream commands one at a time. Stop on first error.** The build script MUST check every single command response. If `result.get("ok") == False` or `result.get("error")`, print the error and STOP immediately. Do NOT continue building on a broken state. This is an interpreter, not a batch pipeline. Pattern:
```python
async def cmd(self, c, **kw):
    ...
    if not result.get("ok", True):
        error = result.get("error", "unknown")
        print(f"  FATAL: {c} failed: {error}")
        raise RuntimeError(f"Command {c} failed: {error}")
    return result.get("data", result)
```

## Node Creation Rules

1. **Never generate IDs in Python.** The browser-side Zod `.parse()` auto-generates proper `{type}_{nanoid}` IDs. Just send the node data without an `id` field.

2. **Use lowercase type values.** The Zod schemas use: `wall`, `slab`, `ceiling`, `zone`, `door`, `window`, `roof`, `roof-segment`, `item`, `level`, `building`, `site`. Never `WallNode`, `SlabNode`, etc.

3. **Door/window position is distance from wall START.** The `position[0]` (x in wall-local space) is the distance in meters from the wall's start point — NOT from the center. The editor's `clampToWall()` and `hasWallChildOverlap()` functions all use start-relative coordinates.

4. **Doors and windows MUST be children of walls.** Set `parentId = wallId`. This is critical for CSG cutout geometry. If parentId is the level, the wall won't have holes cut in it.

5. **Roofs are TWO nodes.** Create a `RoofNode` (container, child of level) with only `position` and `rotation`. Then create a `RoofSegmentNode` (child of the roof) with all geometry: `roofType`, `width`, `depth`, `roofHeight`, `wallHeight`, etc. The RoofNode has NO geometry fields.

6. **Roof positioning — center of footprint.**
   - **RoofNode** `position` = world center of the building footprint. For walls at `(0,0)-(12,0)-(12,8)-(0,8)`, the center is `[6, 0, 4]`.
   - **RoofSegmentNode** `position` = `[0, 0, 0]` (local to parent, centered).
   - `width` = building width (X span), `depth` = building depth (Z span).
   - **Put the roof on its own level.** Create a new level (e.g., level 2 for a 1-story building) as a child of the building. The LevelSystem stacks it on top automatically. Then `wallHeight: 0` (no knee walls needed — height is handled by the level). `roofHeight` = peak height (e.g., 2.0m for a moderate slope).
   - This is the correct pattern: walls on level N, roof on level N+1. The level system handles vertical positioning.
   - Formula: `RoofNode.position = [(minX+maxX)/2, 0, (minZ+maxZ)/2]`
   - `RoofSegmentNode.width = maxX - minX`, `RoofSegmentNode.depth = maxZ - minZ`

6b. **Roofs only on SIMPLE RECTANGULAR volumes.** The CSG evaluator crashes on complex L/T/U shapes. For compound layouts, add a roof per rectangular volume separately. Each roof covers exactly one rectangle of walls. Never try to roof an irregular polygon.

7. **After `clear()`, wait and retry `read_state`.** The scene takes time to reinitialize the default Site > Building > Level hierarchy. Poll with sleep until building_id and level_id are found.

7b. **`clear` resets scene without page reload.** Just send `clear`, wait 1 second, then `read_state` to get the default building/level. No reconnection needed. Pattern:
```python
await b.cmd("clear")
await asyncio.sleep(1)
st = await b.cmd("read_state")
```

8. **Reuse the default building/level.** `loadScene()` auto-creates Site > Building > Level(1). Don't create new ones — find them in state with `type == "building"` and `type == "level"`.

8b. **Level 1 = Ground floor (default). Level 0 = Basement (only if requested).** The default scene gives level 1 (ground floor). Reuse it directly. Upper floors are level 2, 3, 4... Only create level 0 if the user explicitly asks for a basement. Label: 0=B, 1=G, 2=1F, 3=2F, etc.

9. **`children: []` is required** on wall, level, ceiling, roof nodes. The renderers call `.map()` on children. If missing, the scene crashes. The Zod parse handles this, but if it fails, the fallback must include `children: []`.

## Architectural Design Rules

10. **Never make a plain rectangle.** Use L-shapes, T-shapes, U-shapes, or compound layouts with multiple separate volumes. Rich architecture has visual variety in massing.

11. **Not every space needs walls.** Use covered terraces (slab + ceiling + columns, no walls), breezeways (connecting corridors with columns), and open-air structures. Deliberate negative space makes the design breathe.

12. **Don't fill every room with function.** Leave structural voids, open terraces, courtyards. A compound of separate small buildings connected by walkways is more interesting than one giant box.

13. **Use separate volumes.** Instead of one big building, create multiple separate buildings on the same level: main house, guest pavilion, pool house, carport. They each get their own walls and slabs.

14. **Outdoor space is essential.** Every estate needs:
    - Trees (use `tree`, `fir-tree`, `palm` items at negative coordinates / outside walls)
    - Bushes for garden beds
    - Pool area (sunken slab + blue zone + sunbeds + umbrellas)
    - Patio/terrace with outdoor dining
    - Parking (carport with columns, Tesla cars)
    - Sports/play area (basketball hoops, playground)
    - Garden seating areas between buildings

15. **Vary ceiling heights.** Main living spaces get 3.2-3.5m. Service areas can be 2.8m. Open-air structures use columns (scaled-up pillars) instead of walls.

16. **Floor-to-ceiling windows** on main living areas. Use large windows (width=2.5-3.0, height=2.2-2.4, sill=0.3-0.4) for a modern look. Small windows (1.0-1.2m) for bathrooms and utility.

17. **Split-level design.** Not all sections need a second floor. Having the master wing or entertainment wing as single-story while the main block has 2 floors creates visual interest.

18. **Stairwell holes.** When creating upper floors, cut a hole in the slab polygon using the `holes` field for the stairwell area. Don't place oversized stair items — the stairwell void is sufficient.

## Furniture Placement Rules

19. **Place items OUTSIDE walls.** Items at `[x, 0, z]` are in level-space world coordinates. Keep 0.3-0.5m clearance from wall surfaces to avoid penetration.

20. **Furniture rotation is in radians.** `[0, rotation_y, 0]` where rotation_y is around the Y axis. Common values: `0` (default), `math.pi/2` (90°), `math.pi` (180°), `-math.pi/2` (270°).

21. **Outdoor items are children of ground floor (level 1).** Place trees, bushes, cars, etc. as children of the ground floor level, using world coordinates (can be negative for items outside the building footprint).

22. **Scale pillars for columns.** The `pillar` asset is only 1.3m tall. Scale it `[1, 2.5, 1]` to make proper structural columns for terraces and carports.

22b. **Don't overdo landscaping.** Trees and bushes are high-poly 3D models. Too many tanks performance and overwhelms the scene visually. Guidelines:
    - Max 8-10 trees total for a large compound
    - Max 6-8 bushes
    - Max 4-6 palms
    - Space them out — they're accents, not a forest
    - Perimeter screening: use 3-4 fir trees on each side, not a wall of them

22c. **USE THE FULL 140-ITEM CATALOG.** Every room should feel lived-in and distinct. Don't reuse the same few items everywhere. Use decor, accessories, wall art, rugs, plants, and lighting — not just the core furniture. Room recipes:
    - **Living:** sofa/couch-medium/bean-bag + coffee-table + tv-stand + floor-lamp + rectangular-carpet + indoor-plant + picture/wall-art-06 + recessed-light on ceiling
    - **Kitchen:** kitchen-counter + stove + hood + fridge/kitchen-fridge + microwave + dining-table + dining-chairs + fruits + kitchen-utensils + ceiling-light
    - **Bedroom:** double-bed/single-bed + 2x bedside-table + table-lamp + closet + dresser + rectangular-carpet + picture + small-indoor-plant
    - **Bathroom:** toilet + bathroom-sink/wall-sink/sink-cabinet + shower-square/shower-angle/bathtub + toilet-brush + toilet-paper + shower-rug + rectangular-mirror
    - **Office:** desk/office-table + office-chair + bookshelf + books + computer + table-lamp + small-indoor-plant
    - **Hallway:** coat-rack + round-mirror/picture + small-indoor-plant + recessed-light
    - **Gym:** threadmill + exercise-bike + barbell-stand + barbell + rectangular-carpet
    - **Kids room:** bunkbed/single-bed + toy + car-toy + easel + bookshelf + round-carpet
    - Use ceiling lighting (ceiling-lamp, recessed-light, circular-ceiling-light, rectangular-ceiling-light) in every room
    - Use wall-mounted items (picture, wall-art-06, rectangular-mirror, round-mirror, shelf) to fill blank walls
    - Safety items (fire-extinguisher, smoke-detector, exit-sign) in hallways and kitchens

## Accessibility & Circulation Rules

28. **Every enclosed room MUST have at least one door.** Before finishing a floor, verify that every zone/room has a door connecting it to a hallway or adjacent room. A room with no door is inaccessible — this is a critical design failure. Checklist after laying out walls:
    - Count rooms (zones)
    - Count doors
    - Verify: doors >= rooms (some rooms may need 2 doors)
    - Every bathroom has a door
    - Every bedroom has a door
    - Every closet/utility has a door

29. **Every room should have at least one window on an exterior wall.** Exceptions: hallways, stairwells, closets, utility rooms. But bedrooms, living rooms, kitchens, bathrooms, offices MUST have windows. Bathrooms can have smaller windows (1.0m) but still need one.

30. **Multi-story buildings MUST have a stairwell.** If the building has more than 1 level:
    - Designate a stairwell zone on EVERY floor in the same position
    - Cut a hole in the slab on upper floors for the stairwell area
    - The stairwell needs doors connecting to hallways/landings on each floor
    - Without a stairwell, upper floors are unreachable — this breaks the design

31. **Door connectivity graph.** Think of the building as a graph: rooms are nodes, doors are edges. Starting from the front door, every room must be reachable by walking through doors. If any room is disconnected from the graph, add a door. Common mistakes:
    - Bathroom with no door (forgotten)
    - Second wing with no connecting door to hallway
    - Upper floor with no stairwell connection
    - Guest pavilion with no entrance door on exterior wall

32. **Clear-then-reconnect pattern for multi-story.** When building upper floors:
    - Create the level node as child of building
    - The `create_level` response returns the new level ID
    - If it returns None/undefined, read state to find it
    - Set selection to the new level before creating walls on it
    - Cut stairwell hole in the slab with `holes` field

## Construction Panel Integration

33. **The editor has a live construction panel.** Every `create_node` is automatically logged to a floating panel in the browser. The build script must also send:
    - `build_start` — at the beginning (clears panel, shows building indicator)
    - `log` with `message` and `level` — before each major section (e.g., "Ground Floor: Exterior Walls")
    - `build_end` — at the end (shows complete indicator)
    The `B` class needs a `log(msg, level)` helper. Levels: `step` (section headers), `info` (notes), `error`, `done`.

## Browser Error Monitoring

27. **Browser errors are forwarded to Python.** The BridgeProvider intercepts `console.error` and `window.onerror`, sending them to the Python client via `{"type": "browser_error", "payload": "..."}`. The client stores them in `client.browser_errors` and prints `[BROWSER ERROR]` to terminal. After building, check `client.browser_errors` — if non-empty, something went wrong in the renderer.

## WebSocket Protocol Rules

23. **Parameter names must be camelCase** matching TypeScript types: `parentId` (not `parent_id`), `nodeId` (not `node_id`), `nodeIds` (not `ids`).

24. **`set_selection` needs a nested `selection` object.** Send `{"cmd": "set_selection", "selection": {"levelId": "..."}}`, not flat kwargs.

25. **`read_nodes` filter uses `type`** not `node_type`. Send `{"cmd": "read_nodes", "type": "wall"}`.

26. **Response data is in `result.data`.** The `send()` method returns the full response; extract with `result.get("data", result)`.
