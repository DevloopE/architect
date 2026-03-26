# ArchitectBot

AI-powered 3D building generator. Describe a building in natural language, get a fully furnished 3D model in the browser.

https://github.com/pascalorg/editor

## Quick Start

```bash
# 1. Clone with submodule
git clone --recursive https://github.com/YOUR_USERNAME/architectbot.git
cd architectbot

# 2. Setup (installs editor + python deps)
bash setup.sh

# 3. In Claude Code, run:
/build a modern compound estate with pool, guest house, and carport
```

## What It Does

You type a prompt. The AI:
1. Designs the architecture (compound layouts, not rectangles)
2. Writes a build script with exact wall coordinates, doors, windows, furniture
3. Sends commands over WebSocket to the live 3D editor
4. The building appears in your browser at http://localhost:3002

## Requirements

- [Bun](https://bun.sh/) (for the editor)
- [Python 3.11+](https://python.org/) (for the build scripts)
- [Claude Code](https://claude.ai/claude-code) (for the `/build` command)

## Manual Usage

```bash
# Terminal 1: Start editor + relay + browser
bash start.sh

# Terminal 2: Run the build script
python build_one_floor.py
```

## Architecture

```
architectbot/
├── editor/                    # Pascal Editor (git submodule)
│   ├── packages/editor/src/
│   │   └── components/bridge/ # WebSocket bridge (our addition)
│   └── apps/editor/
│       └── bridge-relay.mjs   # WebSocket relay server (our addition)
├── architect/                 # Python AI agents
│   ├── agents/                # LangGraph agents
│   ├── tools/                 # Editor API wrappers
│   └── prompts/               # System prompts + lessons learned
├── .claude/commands/
│   └── build.md               # /build slash command
├── build_one_floor.py         # Generated build script
├── setup.sh                   # One-command setup
└── start.sh                   # Start editor + relay
```

## How It Works

```
/build prompt → Claude reads building-lessons.md
             → Designs compound layout (not a rectangle!)
             → Writes Python build script
             → Script connects via WebSocket to editor
             → Creates walls, doors, windows, furniture, landscape
             → Building appears live in browser
```

## Design Philosophy

Buildings are NOT plain boxes. Every build follows these principles:

- **Compound layouts** — multiple separate volumes (main house, guest pavilion, pool house)
- **Negative space** — covered terraces, breezeways, courtyards
- **Outdoor living** — pool, sports court, garden, parking
- **Split-level** — varying heights for visual interest
- **Floor-to-ceiling windows** — modern, light-filled interiors
- **Full furnishing** — every room has appropriate furniture
