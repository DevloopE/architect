# Architect

**Build any building with Claude Code.**

AI-powered 3D architectural editor with live construction, 140+ furniture items, floor-level switching, and Python/WebSocket automation. Describe a building in natural language and watch it appear in real-time.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/DevloopE/architect.git
cd architect

# 2. Setup (installs editor + electron + python deps)
bash setup.sh

# 3. Run the desktop app
cd electron && npm start

# 4. In Claude Code, run:
/build a modern compound estate with pool, guest house, and carport
```

## What It Does

You type a prompt. The AI:
1. Designs the architecture (compound layouts, courtyards, split-level)
2. Writes a build script with exact wall coordinates, doors, windows, furniture
3. Sends commands over WebSocket to the live 3D editor
4. The building appears in real-time with 140+ items of furniture and decor

## Features

- **140+ furniture items** — seating, tables, beds, kitchen, bathroom, lighting, outdoor, fitness, decor, safety equipment
- **Floor-level switcher** — floating panel to switch between floors with solo/stacked view modes
- **Scene JSON loading** — load both pipeline and scene JSON files
- **Level numbering** — Level 1 = ground floor, Level 0 = basement, Level 2+ = upper floors
- **Electron desktop app** — WebGPU-accelerated native window
- **Live construction panel** — watch every wall, door, and item appear step by step
- **Save/Load pipelines** — save construction sequences and replay them
- **Export** — GLB (standard 3D) and raw scene JSON

## Requirements

- [Bun](https://bun.sh/) (for the editor kernel)
- [Node.js 20+](https://nodejs.org/) (for Electron and relay)
- [Python 3.11+](https://python.org/) (for build scripts)
- [Claude Code](https://claude.ai/claude-code) (for the `/build` command)

## Usage

### Desktop App (Electron)
```bash
cd electron && npm start
```

### Browser Mode
```bash
bash start.sh
# Opens http://localhost:3002
```

### Claude Code
```bash
/build a 3-story luxury hotel with rooftop bar and underground parking
```

### Manual Build
```bash
bash start.sh
python build_one_floor.py
```

## Architecture

```
architect/
├── editor/                    # Editor kernel (Pascal Editor)
│   ├── packages/core/         # Scene schema, state, spatial logic
│   ├── packages/editor/       # Editor UI, tools, level-switcher
│   ├── packages/viewer/       # 3D canvas (React Three Fiber + WebGPU)
│   └── apps/editor/           # Next.js app + WebSocket relay
├── electron/                  # Desktop app (Electron + WebGPU)
│   └── main.js                # Electron main process
├── architect/                 # Python AI agents + prompts
│   └── prompts/               # System prompts + building lessons
├── .claude/commands/
│   └── build.md               # /build slash command (140 items catalog)
├── build_house.py             # Example: 2-story house with furniture
├── build_one_floor.py         # Example: courtyard hotel compound
├── save_scene.py              # Save/load scenes via Python
├── setup.sh                   # One-command setup
└── start.sh                   # Start editor + relay + browser
```

## How It Works

```
/build prompt → Claude reads building-lessons.md
             → Designs compound layout (not a rectangle!)
             → Writes Python build script
             → Script connects via WebSocket to editor
             → Creates walls, doors, windows, furniture, landscape
             → Building appears live in browser/desktop
```

## Design Philosophy

Buildings are NOT plain boxes. Every build follows these principles:

- **Compound layouts** — multiple separate volumes (main house, guest pavilion, pool house)
- **Negative space** — covered terraces, breezeways, courtyards
- **Outdoor living** — pool, sports court, garden, parking
- **Split-level** — varying heights for visual interest
- **Floor-to-ceiling windows** — modern, light-filled interiors
- **Full furnishing** — 140+ items, every room feels lived-in with decor, plants, lighting, and accessories
- **Accessibility** — every room has a door, every habitable room has a window, multi-story = stairwell

## License

MIT
