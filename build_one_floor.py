"""Single floor house with furniture."""

import asyncio, json, math, uuid, websockets

WS_URL = "ws://localhost:3100"

class B:
    def __init__(self):
        self.ws = self.pending = self.listener = None
    async def connect(self):
        self.ws = await websockets.connect(WS_URL)
        await self.ws.send(json.dumps({"type":"register","role":"python"}))
        self.pending = {}
        self.listener = asyncio.create_task(self._listen())
        await asyncio.sleep(0.5)
    async def _listen(self):
        try:
            async for raw in self.ws:
                m = json.loads(raw)
                p = m.get("payload", m)
                mid = p.get("id")
                if mid and mid in self.pending: self.pending[mid].set_result(p)
        except: pass
    async def cmd(self, command, **params):
        mid = uuid.uuid4().hex[:12]
        f = asyncio.get_running_loop().create_future()
        self.pending[mid] = f
        await self.ws.send(json.dumps({"type":"command","payload":{"cmd":command,"id":mid,**params}}))
        try: r = await asyncio.wait_for(f, timeout=10)
        except asyncio.TimeoutError: print(f"  TIMEOUT: {command}"); return {"ok":False}
        finally: self.pending.pop(mid, None)
        return r.get("data", r)
    async def close(self):
        if self.listener: self.listener.cancel()
        if self.ws: await self.ws.close()

def wlx(s, e, pos):
    """position_along_wall is already distance-from-start.
    The editor uses start-relative x for door/window position[0]."""
    return pos

def asset(id, name, cat, src, dims, offset=None):
    return {"id":id,"category":cat,"name":name,"thumbnail":"","src":src,
            "dimensions":dims,"offset":offset or [0,0,0],"rotation":[0,0,0],"scale":[1,1,1]}

SOFA = asset("sofa","Sofa","furniture","/items/sofa/model.glb",[2.5,0.8,1.5],[0,0,0.04])
COFFEE = asset("coffee-table","Coffee Table","furniture","/items/coffee-table/model.glb",[2,0.4,1.5])
TVSTAND = asset("tv-stand","TV Stand","furniture","/items/tv-stand/model.glb",[2,0.4,0.5],[0,0.21,0])
FLAMP = asset("floor-lamp","Floor Lamp","furniture","/items/floor-lamp/model.glb",[1,1.9,1])
DTABLE = asset("dining-table","Dining Table","furniture","/items/dining-table/model.glb",[2.5,0.8,1],[0,0,-0.01])
DCHAIR = asset("dining-chair","Dining Chair","furniture","/items/dining-chair/model.glb",[0.5,1,0.5])
FRIDGE = asset("fridge","Fridge","kitchen","/items/fridge/model.glb",[1,2,1],[0.01,0,-0.05])
STOVE = asset("stove","Stove","kitchen","/items/stove/model.glb",[1,1,1],[0,0,-0.05])
KCOUNTER = asset("kitchen-counter","Kitchen Counter","kitchen","/items/kitchen-counter/model.glb",[2,0.8,1])
DBED = asset("double-bed","Double Bed","furniture","/items/double-bed/model.glb",[2,0.8,2.5],[0,0,-0.03])
BSIDE = asset("bedside-table","Bedside Table","furniture","/items/bedside-table/model.glb",[0.5,0.5,0.5],[0,0,-0.01])
CLOSET = asset("closet","Closet","furniture","/items/closet/model.glb",[2,2.5,1],[0,0,-0.01])
DRESSER = asset("dresser","Dresser","furniture","/items/dresser/model.glb",[1.5,0.8,1])
TOILET = asset("toilet","Toilet","bathroom","/items/toilet/model.glb",[1,0.9,1],[0,0,-0.23])
SINK = asset("bathroom-sink","Bathroom Sink","bathroom","/items/bathroom-sink/model.glb",[2,1,1.5],[0.11,0,0.02])
SHOWER = asset("shower-square","Squared Shower","bathroom","/items/shower-square/model.glb",[1,2,1],[0.41,0,-0.42])

async def main():
    b = B()
    await b.connect()
    print("[Builder] Connected")

    await b.cmd("clear")
    # Wait for scene to reinitialize with default hierarchy
    bid = lid = None
    for attempt in range(10):
        await asyncio.sleep(1)
        state = await b.cmd("read_state")
        nodes = state.get("nodes",{})
        for nid, n in nodes.items():
            if n.get("type")=="building": bid = nid
            if n.get("type")=="level": lid = nid
        if bid and lid:
            break
    print(f"Building: {bid}, Level: {lid}")
    if not bid or not lid:
        print("ERROR: Could not find default scene"); await b.close(); return

    # ====== SINGLE FLOOR: 14m x 10m ======
    # Layout:
    #  (0,0)-------(7,0)-------(14,0)
    #  |            |            |
    #  | Bedroom    | Living     |
    #  | 3.5x5      | Room 7x5  |
    #  |            |            |
    #  (0,5)-(3.5,5)(7,5)------(14,5)
    #  | Bath |     |            |
    #  | 3.5x5| Bed | Kitchen    |
    #  |      | room| 7x5       |
    #  (0,10)(3.5,10)(7,10)----(14,10)

    print("\n--- Building single floor ---")
    await b.cmd("set_selection", selection={"levelId": lid})

    # Slab
    await b.cmd("create_node", node={"type":"slab","polygon":[[0,0],[14,0],[14,10],[0,10]],"elevation":0.05}, parentId=lid)

    # Exterior walls
    w = []
    for s, e in [([0,0],[14,0]),([14,0],[14,10]),([14,10],[0,10]),([0,10],[0,0])]:
        r = await b.cmd("create_node", node={"type":"wall","start":s,"end":e,
            "thickness":0.2,"height":2.8,"frontSide":"exterior","backSide":"interior"}, parentId=lid)
        w.append({"id":r.get("nodeId"),"s":s,"e":e})

    # Interior walls
    for s, e in [
        ([7,0],[7,10]),     # 4: vertical center divider
        ([0,5],[7,5]),      # 5: horizontal left side
        ([3.5,5],[3.5,10]), # 6: bath/bedroom divider
    ]:
        r = await b.cmd("create_node", node={"type":"wall","start":s,"end":e,
            "thickness":0.1,"height":2.8}, parentId=lid)
        w.append({"id":r.get("nodeId"),"s":s,"e":e})

    # Doors
    print("  Doors...")
    # Front door - north wall at x=10
    ww = w[0]; await b.cmd("create_node", node={"type":"door","position":[wlx(ww["s"],ww["e"],10),1.05,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":1.0,"height":2.1}, parentId=ww["id"])
    # Bedroom door - horiz wall (w5) at x=2
    ww = w[5]; await b.cmd("create_node", node={"type":"door","position":[wlx(ww["s"],ww["e"],2),1.05,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":0.8,"height":2.1}, parentId=ww["id"])
    # Living->Kitchen - vertical center (w4) at z=7.5
    ww = w[4]; await b.cmd("create_node", node={"type":"door","position":[wlx(ww["s"],ww["e"],7.5),1.05,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":0.8,"height":2.1}, parentId=ww["id"])
    # Bathroom door - bath divider (w6) at z=7.5
    ww = w[6]; await b.cmd("create_node", node={"type":"door","position":[wlx(ww["s"],ww["e"],2.5),1.05,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":0.7,"height":2.1}, parentId=ww["id"])
    # Bedroom 2 door - horiz wall (w5) at x=5.5
    ww = w[5]; await b.cmd("create_node", node={"type":"door","position":[wlx(ww["s"],ww["e"],5.5),1.05,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":0.8,"height":2.1}, parentId=ww["id"])

    # Windows
    print("  Windows...")
    # Bedroom 1 - west wall at z=2.5
    ww = w[3]; await b.cmd("create_node", node={"type":"window","position":[wlx(ww["s"],ww["e"],7.5),1.65,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":1.5,"height":1.5}, parentId=ww["id"])
    # Living room - north wall at x=10
    ww = w[0]; await b.cmd("create_node", node={"type":"window","position":[wlx(ww["s"],ww["e"],3),1.65,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":1.8,"height":1.5}, parentId=ww["id"])
    # Living room - east wall at z=2.5
    ww = w[1]; await b.cmd("create_node", node={"type":"window","position":[wlx(ww["s"],ww["e"],2.5),1.65,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":1.5,"height":1.5}, parentId=ww["id"])
    # Kitchen - east wall at z=7.5
    ww = w[1]; await b.cmd("create_node", node={"type":"window","position":[wlx(ww["s"],ww["e"],7.5),1.65,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":1.5,"height":1.5}, parentId=ww["id"])
    # Kitchen - south wall at x=10
    ww = w[2]; await b.cmd("create_node", node={"type":"window","position":[wlx(ww["s"],ww["e"],4),1.65,0],
        "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":1.5,"height":1.5}, parentId=ww["id"])

    # Zones
    print("  Zones...")
    for nm, poly, col in [
        ("Bedroom",     [[0,0],[7,0],[7,5],[0,5]],       "#8b5cf6"),
        ("Living Room", [[7,0],[14,0],[14,10],[7,10]],    "#3b82f6"),
        ("Bathroom",    [[0,5],[3.5,5],[3.5,10],[0,10]],  "#06b6d4"),
        ("Bedroom 2",   [[3.5,5],[7,5],[7,10],[3.5,10]],  "#a855f7"),
    ]:
        await b.cmd("create_node", node={"type":"zone","name":nm,"polygon":poly,"color":col}, parentId=lid)

    # Ceiling
    await b.cmd("create_node", node={"type":"ceiling","polygon":[[0,0],[14,0],[14,10],[0,10]],"height":2.8}, parentId=lid)

    # Roof
    print("  Roof...")
    r = await b.cmd("create_node", node={"type":"roof","position":[0,0,0],"rotation":0}, parentId=lid)
    roof_id = r.get("nodeId")
    await b.cmd("create_node", node={"type":"roof-segment","roofType":"hip",
        "position":[7,0,5],"rotation":0,"width":14,"depth":10,
        "wallHeight":0.3,"roofHeight":2.0,
        "wallThickness":0.1,"deckThickness":0.1,"overhang":0.4,"shingleThickness":0.05}, parentId=roof_id)

    # ====== FURNITURE ======
    async def place(a, pos, rot=0):
        await b.cmd("create_node", node={"type":"item","asset":a,
            "position":pos,"rotation":[0,rot,0],"scale":[1,1,1]}, parentId=lid)

    # Bedroom (0,0)-(7,5)
    print("  Furnishing bedroom...")
    await place(DBED, [3.5, 0, 1.5], math.pi/2)
    await place(BSIDE, [1.5, 0, 0.5])
    await place(BSIDE, [5.5, 0, 0.5])
    await place(CLOSET, [0.6, 0, 4], 0)
    await place(DRESSER, [5.5, 0, 4])

    # Living Room (7,0)-(14,10) - large open space
    print("  Furnishing living room...")
    await place(SOFA, [10.5, 0, 3], math.pi)
    await place(COFFEE, [10.5, 0, 1.8])
    await place(TVSTAND, [10.5, 0, 0.5])
    await place(FLAMP, [8, 0, 0.8])
    await place(DTABLE, [10.5, 0, 7])
    await place(DCHAIR, [10.5, 0, 6.2], math.pi)
    await place(DCHAIR, [10.5, 0, 7.8], 0)
    await place(DCHAIR, [9.2, 0, 7], math.pi/2)
    await place(DCHAIR, [11.8, 0, 7], -math.pi/2)
    await place(FRIDGE, [8, 0, 9.3], math.pi)
    await place(STOVE, [9, 0, 9.3], math.pi)
    await place(KCOUNTER, [8.5, 0, 5.5])

    # Bathroom (0,5)-(3.5,10)
    print("  Furnishing bathroom...")
    await place(TOILET, [1.5, 0, 9], math.pi)
    await place(SINK, [1.5, 0, 6])
    await place(SHOWER, [0.8, 0, 7.5])

    # Bedroom 2 (3.5,5)-(7,10)
    print("  Furnishing bedroom 2...")
    await place(DBED, [5.25, 0, 9], math.pi)
    await place(BSIDE, [4, 0, 9])
    await place(CLOSET, [4.5, 0, 5.6], math.pi/2)

    print("\n" + "="*50)
    print("  DONE! Single-floor house with furniture")
    print("  4 rooms: Bedroom, Living Room, Bathroom, Bedroom 2")
    print("  Hip roof with overhang")
    print("  View at http://localhost:3002")
    print("="*50)
    await b.close()

if __name__ == "__main__":
    asyncio.run(main())
