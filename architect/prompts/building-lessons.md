# Building Lessons — Learned from Real Editor Testing

These are hard-won lessons from building in the Pascal Editor. Every agent MUST follow these rules.

## Node Creation Rules

1. **Never generate IDs in Python.** The browser-side Zod `.parse()` auto-generates proper `{type}_{nanoid}` IDs. Just send the node data without an `id` field.

2. **Use lowercase type values.** The Zod schemas use: `wall`, `slab`, `ceiling`, `zone`, `door`, `window`, `roof`, `roof-segment`, `item`, `level`, `building`, `site`. Never `WallNode`, `SlabNode`, etc.

3. **Door/window position is distance from wall START.** The `position[0]` (x in wall-local space) is the distance in meters from the wall's start point — NOT from the center. The editor's `clampToWall()` and `hasWallChildOverlap()` functions all use start-relative coordinates.

4. **Doors and windows MUST be children of walls.** Set `parentId = wallId`. This is critical for CSG cutout geometry. If parentId is the level, the wall won't have holes cut in it.

5. **Roofs are TWO nodes.** Create a `RoofNode` (container, child of level) with only `position` and `rotation`. Then create a `RoofSegmentNode` (child of the roof) with all geometry: `roofType`, `width`, `depth`, `roofHeight`, `wallHeight`, etc. The RoofNode has NO geometry fields.

6. **Roof position matters.** The RoofSegmentNode `position` should be at the center of the building footprint. The RoofNode position should be `[0,0,0]`.

7. **After `clear()`, wait and retry `read_state`.** The scene takes time to reinitialize the default Site > Building > Level hierarchy. Poll with sleep until building_id and level_id are found.

8. **Reuse the default building/level.** `loadScene()` auto-creates Site > Building > Level(0). Don't create new ones — find them in state with `type == "building"` and `type == "level"`.

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

## WebSocket Protocol Rules

23. **Parameter names must be camelCase** matching TypeScript types: `parentId` (not `parent_id`), `nodeId` (not `node_id`), `nodeIds` (not `ids`).

24. **`set_selection` needs a nested `selection` object.** Send `{"cmd": "set_selection", "selection": {"levelId": "..."}}`, not flat kwargs.

25. **`read_nodes` filter uses `type`** not `node_type`. Send `{"cmd": "read_nodes", "type": "wall"}`.

26. **Response data is in `result.data`.** The `send()` method returns the full response; extract with `result.get("data", result)`.
