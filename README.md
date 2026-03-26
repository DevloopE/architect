# Architect

**Build any building with AI. In real-time. In 3D.**

Describe a building in plain English. Watch it construct itself — walls, doors, windows, furniture, landscaping — live in a full 3D editor. Powered by Claude Code.

---

## Demo

```
/build a modern 2-story villa with infinity pool, guest pavilion, and rooftop terrace
```

The AI designs the architecture, writes the construction script, and streams every element into a live 3D scene. Walls go up. Doors cut through. Furniture fills rooms. Trees line the perimeter. All in real-time.

---

## Why Architect

Most AI building tools give you a floor plan image. Architect gives you a **real 3D model** you can walk through, export as GLB, and modify in a full editor.

- **Not a renderer** — it's a construction engine. Every wall, door, and chair is a real scene node.
- **Not a chatbot** — it writes and executes Python build scripts over WebSocket.
- **Not a toy** — 140+ furniture items, multi-story buildings, compound layouts, roofs, landscaping.

---

## Quick Start

```bash
git clone https://github.com/DevloopE/architect.git
cd architect
```

**Windows (PowerShell):**
```powershell
.\setup.ps1                          # install dependencies
cd electron; npm start               # desktop app
# or
.\start.ps1                          # browser mode
```

**Mac / Linux:**
```bash
bash setup.sh                        # install dependencies
cd electron && npm start             # desktop app
# or
bash start.sh                        # browser mode
```

**Build something (in Claude Code):**
```
/build a japanese courtyard house with zen garden and tea room
```

---

## What You Get

| Feature | Details |
|---------|---------|
| **140+ items** | Furniture, kitchen, bathroom, lighting, outdoor, fitness, safety, decor |
| **Multi-story** | Ground floor, upper floors, basements — with automatic stairwell logic |
| **Floor switcher** | Click any floor in the 3D viewport. Solo mode hides other floors instantly |
| **Compound layouts** | L-shapes, U-shapes, separate pavilions, covered walkways, courtyards |
| **Live construction** | Watch every element appear step by step with sound effects |
| **Save/Load** | Save construction pipelines as `.architect.json`, replay them anytime |
| **Scene import** | Load raw scene JSON files directly |
| **Export** | GLB (standard 3D format) or raw scene JSON |
| **Electron app** | Native desktop window with WebGPU acceleration |
| **Full editor** | Draw walls, place items, edit zones, adjust roofs — all manually too |

---

## How It Works

```
You: /build a 3-story luxury hotel with underground parking

Claude Code:
  1. Reads 30+ architectural rules from building-lessons.md
  2. Designs compound layout (never a plain rectangle)
  3. Writes Python build script with exact coordinates
  4. Script connects to editor via WebSocket (port 3100)
  5. Streams create_node commands: walls, slabs, doors, windows
  6. Furnishes every room from 140-item catalog
  7. Adds landscaping: trees, bushes, pool, parking
  8. Building appears live at localhost:3002
```

---

## Architecture

```
architect/
├── editor/                    # 3D Editor kernel
│   ├── packages/core/         #   Scene schema, state management, spatial logic
│   ├── packages/editor/       #   UI components, tools, floor switcher
│   ├── packages/viewer/       #   3D rendering (React Three Fiber + WebGPU)
│   └── apps/editor/           #   Next.js app + WebSocket relay server
├── electron/                  # Desktop app wrapper
│   └── main.js                #   Electron with WebGPU flags
├── architect/                 # AI agent prompts
│   └── prompts/               #   Building lessons + system prompts
├── .claude/commands/
│   └── build.md               #   /build slash command definition
├── build_house.py             # Example: 2-story furnished house
├── build_one_floor.py         # Example: courtyard hotel compound
├── save_scene.py              # Save/load scenes via CLI
├── setup.sh                   # One-command install
└── start.sh                   # Launch editor + relay + browser
```

---

## Requirements

- [Bun](https://bun.sh/) — runs the editor
- [Node.js 20+](https://nodejs.org/) — runs Electron and the relay server
- [Python 3.11+](https://python.org/) — runs build scripts
- [Claude Code](https://claude.ai/claude-code) — the AI that designs and builds

---

## The 140-Item Catalog

Every room is furnished from a real catalog of 3D models:

**Living** — sofa, bean bag, couches, coffee table, TV stand, floor lamp, carpets, plants, wall art, piano

**Kitchen** — counter, stove, hood, fridge, freezer, microwave, cabinets, dining table, chairs, utensils

**Bedroom** — double/single/bunk bed, nightstands, closet, dresser, table lamp, mirror, carpet

**Bathroom** — toilet, sink, wall sink, shower, bathtub, cabinet, toilet brush, shower rug, mirror

**Office** — desk, office chair, bookshelf, computer, books, table lamp

**Lighting** — floor lamp, table lamp, ceiling lamp, recessed light, circular/rectangular ceiling lights

**Outdoor** — trees, palms, bushes, hedges, fences, pool umbrella, sunbed, cars, basketball hoop

**Safety** — fire extinguisher, smoke detector, fire alarm, exit sign, sprinkler, alarm keypad

---

## Design Philosophy

The AI follows 30+ architectural rules to ensure every building is realistic:

- **No plain rectangles.** Compound layouts with separate volumes, courtyards, and covered walkways.
- **Every room has a door.** The AI verifies door connectivity — no inaccessible rooms.
- **Every habitable room has a window.** Bedrooms, kitchens, offices all get natural light.
- **Multi-story means stairwell.** Automatic slab holes and stairwell zones on every floor.
- **Outdoor space is essential.** Gardens, pools, parking, sports areas — not just the building.
- **Rooms feel lived-in.** Decor, plants, rugs, wall art, ceiling lights — not just the main furniture.

---

## License

MIT
