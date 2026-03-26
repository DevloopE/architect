"""Save or load a scene to/from a JSON file."""
import asyncio, sys, json, websockets, uuid

WS = "ws://localhost:3100"

class Client:
    def __init__(self):
        self.ws = self.pending = self.listener = None
    async def connect(self):
        self.ws = await websockets.connect(WS)
        await self.ws.send(json.dumps({"type": "register", "role": "python"}))
        self.pending = {}
        self.listener = asyncio.create_task(self._listen())
        await asyncio.sleep(0.5)
    async def _listen(self):
        try:
            async for raw in self.ws:
                m = json.loads(raw)
                p = m.get("payload", m)
                mid = p.get("id")
                if mid and mid in self.pending:
                    self.pending[mid].set_result(p)
        except: pass
    async def cmd(self, c, **kw):
        mid = uuid.uuid4().hex[:12]
        f = asyncio.get_running_loop().create_future()
        self.pending[mid] = f
        await self.ws.send(json.dumps({"type": "command", "payload": {"cmd": c, "id": mid, **kw}}))
        r = await asyncio.wait_for(f, timeout=10)
        self.pending.pop(mid, None)
        return r.get("data", r)
    async def close(self):
        if self.listener: self.listener.cancel()
        if self.ws: await self.ws.close()

async def save(filepath):
    c = Client()
    await c.connect()
    data = await c.cmd("export")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    await c.close()
    print(f"Scene saved to {filepath}")

async def load(filepath):
    c = Client()
    await c.connect()
    with open(filepath) as f:
        data = json.load(f)
    await c.cmd("import", nodes=data["nodes"], rootNodeIds=data["rootNodeIds"])
    await c.close()
    print(f"Scene loaded from {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("save", "load"):
        print("Usage:")
        print("  python save_scene.py save my_building.json")
        print("  python save_scene.py load my_building.json")
        sys.exit(1)

    action, filepath = sys.argv[1], sys.argv[2]
    if action == "save":
        asyncio.run(save(filepath))
    else:
        asyncio.run(load(filepath))
