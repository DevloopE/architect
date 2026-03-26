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

6. **Roof position matters.** The RoofSegmentNode `position` should be at the center of the building footprint. The RoofNode position should be `[0,0,0]`.

6b. **Roofs are fragile — avoid unless explicitly requested.** The RoofSystem's CSG evaluator crashes easily with bad geometry. Only create roofs when the user specifically asks. Use flat roofs (`roofType: "flat"`) as the safest option. Never create roofs on buildings with complex or L/T/U-shaped footprints — they only work on simple rectangular volumes.

7. **After `clear()`, wait and retry `read_state`.** The scene takes time to reinitialize the default Site > Building > Level hierarchy. Poll with sleep until building_id and level_id are found.

7b. **Always clear + reload browser before building.** Every new build must start completely fresh. The script should:
   1. Send `clear` command
   2. Then send a JS eval to wipe IndexedDB: send a `clear` command which calls `clearScene()` (this already handles it)
   3. Refresh the browser page to flush all cached 3D objects from memory
   Pattern: after `clear()`, also send `window.location.reload()` by having the BridgeProvider handle a `reload` command, OR just accept that `clear` is sufficient since it calls `unloadScene()` + `loadScene()` which resets everything.

8. **Reuse the default building/level.** `loadScene()` auto-creates Site > Building > Level(0). Don't create new ones — find them in state with `type == "building"` and `type == "level"`.

8b. **Ground floor is level 0, label it as "G" or "Ground".** Upper floors are level 1, 2, 3... Only create a basement (level -1) if explicitly requested. The default scene gives you level 0 (ground) — reuse it. When creating upper floors, use `level: 1`, `level: 2`, etc.

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

21. **Outdoor items are children of level 0.** Place trees, bushes, cars, etc. as children of the ground floor level, using world coordinates (can be negative for items outside the building footprint).

22. **Scale pillars for columns.** The `pillar` asset is only 1.3m tall. Scale it `[1, 2.5, 1]` to make proper structural columns for terraces and carports.

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
