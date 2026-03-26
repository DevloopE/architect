"""Roof test — roof on its own level so LevelSystem handles height."""
import asyncio, json, uuid, websockets

WS = "ws://localhost:3100"

class B:
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
                m = json.loads(raw); p = m.get("payload", m); mid = p.get("id")
                if mid and mid in self.pending: self.pending[mid].set_result(p)
        except: pass
    async def cmd(self, c, **kw):
        mid = uuid.uuid4().hex[:12]
        f = asyncio.get_running_loop().create_future()
        self.pending[mid] = f
        await self.ws.send(json.dumps({"type": "command", "payload": {"cmd": c, "id": mid, **kw}}))
        try: r = await asyncio.wait_for(f, timeout=10)
        except asyncio.TimeoutError: return {"ok": False}
        finally: self.pending.pop(mid, None)
        return r.get("data", r)
    async def close(self):
        if self.listener: self.listener.cancel()
        if self.ws: await self.ws.close()

async def main():
    b = B(); await b.connect()
    print("[Roof Test] Connected")

    try: await b.cmd("clear")
    except: pass
    await b.close()
    await asyncio.sleep(10)
    await b.connect()

    bid = lid = None
    for _ in range(15):
        await asyncio.sleep(1)
        try:
            st = await b.cmd("read_state")
            for nid, n in st.get("nodes", {}).items():
                if n.get("type") == "building": bid = nid
                if n.get("type") == "level": lid = nid
            if bid and lid: break
        except: pass
    print(f"  Building: {bid}, Level 0: {lid}")

    # Level 0: 12x8 box with walls
    print("  Creating walls (12x8, height 2.8m)...")
    for s, e in [([0,0],[12,0]), ([12,0],[12,8]), ([12,8],[0,8]), ([0,8],[0,0])]:
        await b.cmd("create_node", node={"type": "wall", "start": s, "end": e,
            "thickness": 0.2, "height": 2.8, "frontSide": "exterior", "backSide": "interior"}, parentId=lid)

    await b.cmd("create_node", node={"type": "slab", "polygon": [[0,0],[12,0],[12,8],[0,8]], "elevation": 0.05}, parentId=lid)
    await b.cmd("create_node", node={"type": "ceiling", "polygon": [[0,0],[12,0],[12,8],[0,8]], "height": 2.8}, parentId=lid)

    # Level 1: Roof level — LevelSystem stacks it on top of level 0
    print("  Creating roof level...")
    r = await b.cmd("create_node", node={"type": "level", "level": 1}, parentId=bid)
    roof_level_id = r.get("nodeId")
    print(f"  Roof level: {roof_level_id}")

    # Roof on its own level — wallHeight=0 (no knee walls, it's already at correct height)
    print("  Creating roof (gable, on roof level)...")
    r = await b.cmd("create_node", node={
        "type": "roof",
        "position": [6, 0, 4],
        "rotation": 0,
    }, parentId=roof_level_id)
    roof_id = r.get("nodeId")

    await b.cmd("create_node", node={
        "type": "roof-segment",
        "roofType": "gable",
        "position": [0, 0, 0],
        "rotation": 0,
        "width": 12,
        "depth": 8,
        "wallHeight": 0,
        "roofHeight": 2.0,
        "wallThickness": 0.1,
        "deckThickness": 0.1,
        "overhang": 0.3,
        "shingleThickness": 0.05,
    }, parentId=roof_id)

    print("  DONE! Roof on its own level — height handled by LevelSystem.")
    await b.close()

if __name__ == "__main__":
    asyncio.run(main())
