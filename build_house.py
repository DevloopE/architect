"""Direct builder — fixed roof + furniture."""

import asyncio, json, math, uuid, subprocess, websockets

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
        except asyncio.TimeoutError:
            print(f"  TIMEOUT: {command}"); return {"ok":False}
        finally: self.pending.pop(mid, None)
        return r.get("data", r)
    async def close(self):
        if self.listener: self.listener.cancel()
        if self.ws: await self.ws.close()

def wlx(s, e, pos):
    return pos - math.sqrt((e[0]-s[0])**2 + (e[1]-s[1])**2) / 2

def item(id, name, cat, src, dims, offset=None):
    return {"id":id,"category":cat,"name":name,"thumbnail":"","src":src,
            "dimensions":dims,"offset":offset or [0,0,0],"rotation":[0,0,0],"scale":[1,1,1]}

SOFA = item("sofa","Sofa","furniture","/items/sofa/model.glb",[2.5,0.8,1.5],[0,0,0.04])
COFFEE = item("coffee-table","Coffee Table","furniture","/items/coffee-table/model.glb",[2,0.4,1.5])
TVSTAND = item("tv-stand","TV Stand","furniture","/items/tv-stand/model.glb",[2,0.4,0.5],[0,0.21,0])
TV = item("television","Television","appliance","/items/television/model.glb",[2,1.1,0.5])
DTABLE = item("dining-table","Dining Table","furniture","/items/dining-table/model.glb",[2.5,0.8,1],[0,0,-0.01])
DCHAIR = item("dining-chair","Dining Chair","furniture","/items/dining-chair/model.glb",[0.5,1,0.5])
FRIDGE = item("fridge","Fridge","kitchen","/items/fridge/model.glb",[1,2,1],[0.01,0,-0.05])
STOVE = item("stove","Stove","kitchen","/items/stove/model.glb",[1,1,1],[0,0,-0.05])
KCOUNTER = item("kitchen-counter","Kitchen Counter","kitchen","/items/kitchen-counter/model.glb",[2,0.8,1])
DBED = item("double-bed","Double Bed","furniture","/items/double-bed/model.glb",[2,0.8,2.5],[0,0,-0.03])
SBED = item("single-bed","Single Bed","furniture","/items/single-bed/model.glb",[1.5,0.7,2.5])
BSIDE = item("bedside-table","Bedside Table","furniture","/items/bedside-table/model.glb",[0.5,0.5,0.5],[0,0,-0.01])
CLOSET = item("closet","Closet","furniture","/items/closet/model.glb",[2,2.5,1],[0,0,-0.01])
DRESSER = item("dresser","Dresser","furniture","/items/dresser/model.glb",[1.5,0.8,1])
TOILET = item("toilet","Toilet","bathroom","/items/toilet/model.glb",[1,0.9,1],[0,0,-0.23])
SINK = item("bathroom-sink","Bathroom Sink","bathroom","/items/bathroom-sink/model.glb",[2,1,1.5],[0.11,0,0.02])
SHOWER = item("shower-square","Squared Shower","bathroom","/items/shower-square/model.glb",[1,2,1],[0.41,0,-0.42])
FLAMP = item("floor-lamp","Floor Lamp","furniture","/items/floor-lamp/model.glb",[1,1.9,1])

async def main():
    b = B()
    await b.connect()
    print("[Builder] Connected")

    # Verify browser
    test = await b.cmd("read_state")
    if isinstance(test, dict) and not test.get("nodes"):
        print("Browser not connected, opening...")
        subprocess.Popen(["cmd","/c","start","http://localhost:3002"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for i in range(20):
            await asyncio.sleep(2)
            test = await b.cmd("read_state")
            if isinstance(test, dict) and test.get("nodes"): break
        else:
            print("FAILED to connect"); await b.close(); return

    # Clear + get defaults
    await b.cmd("clear"); await asyncio.sleep(1)
    state = await b.cmd("read_state")
    nodes = state.get("nodes",{})
    bid = lid0 = None
    for nid, n in nodes.items():
        if n.get("type")=="building": bid = nid
        if n.get("type")=="level": lid0 = nid
    print(f"Building: {bid}, Level0: {lid0}")

    # =================== GROUND FLOOR ===================
    print("\n--- Ground Floor ---")
    await b.cmd("set_selection", selection={"levelId": lid0})

    # Slab
    await b.cmd("create_node", node={"type":"slab","polygon":[[0,0],[12,0],[12,10],[0,10]],"elevation":0.05}, parentId=lid0)

    # Walls
    w = []
    for s, e in [([0,0],[12,0]),([12,0],[12,10]),([12,10],[0,10]),([0,10],[0,0]),  # exterior
                 ([7,0],[7,5]),([0,5],[12,5]),([7,5],[7,10])]:  # interior
        r = await b.cmd("create_node", node={"type":"wall","start":s,"end":e,
            "thickness":0.2 if len(w)<4 else 0.1,"height":2.8,
            **({"frontSide":"exterior","backSide":"interior"} if len(w)<4 else {})}, parentId=lid0)
        w.append({"id":r.get("nodeId"),"s":s,"e":e})

    # Doors
    for wi, pos in [(0,3),(5,3),(5,9),(6,2.5)]:
        ww = w[wi]
        await b.cmd("create_node", node={"type":"door","position":[wlx(ww["s"],ww["e"],pos),1.05,0],
            "rotation":[0,0,0],"wallId":ww["id"],"side":"front",
            "width":1.0 if wi==0 else 0.8,"height":2.1}, parentId=ww["id"])

    # Windows
    for wi, pos in [(0,9),(3,7.5),(1,2.5)]:
        ww = w[wi]
        await b.cmd("create_node", node={"type":"window","position":[wlx(ww["s"],ww["e"],pos),1.65,0],
            "rotation":[0,0,0],"wallId":ww["id"],"side":"front",
            "width":1.5 if wi!=3 else 1.8,"height":1.5}, parentId=ww["id"])

    # Zones
    for nm, poly, col in [("Living Room",[[0,0],[7,0],[7,5],[0,5]],"#3b82f6"),
                           ("Kitchen",[[7,0],[12,0],[12,5],[7,5]],"#f59e0b"),
                           ("Hallway",[[0,5],[7,5],[7,10],[0,10]],"#6b7280"),
                           ("Bathroom",[[7,5],[12,5],[12,10],[7,10]],"#06b6d4")]:
        await b.cmd("create_node", node={"type":"zone","name":nm,"polygon":poly,"color":col}, parentId=lid0)

    await b.cmd("create_node", node={"type":"ceiling","polygon":[[0,0],[12,0],[12,10],[0,10]],"height":2.8}, parentId=lid0)

    # --- Furniture: Living Room (0,0)-(7,5) ---
    print("  Furnishing living room...")
    async def place(level, asset, pos, rot=0):
        await b.cmd("create_node", node={"type":"item","asset":asset,
            "position":pos,"rotation":[0,rot,0],"scale":[1,1,1]}, parentId=level)

    await place(lid0, SOFA, [3.5, 0, 2.5], math.pi)        # sofa facing north
    await place(lid0, COFFEE, [3.5, 0, 1.5])                 # coffee table
    await place(lid0, TVSTAND, [3.5, 0, 0.5])                # TV stand against north wall
    await place(lid0, FLAMP, [1, 0, 0.8])                    # floor lamp corner

    # --- Furniture: Kitchen (7,0)-(12,5) ---
    print("  Furnishing kitchen...")
    await place(lid0, FRIDGE, [11.3, 0, 0.5], math.pi)       # fridge NE corner
    await place(lid0, STOVE, [11.3, 0, 2], math.pi)          # stove next to fridge
    await place(lid0, KCOUNTER, [8.5, 0, 4.5], 0)            # counter along south wall
    await place(lid0, DTABLE, [9.5, 0, 2.5])                 # dining table center
    await place(lid0, DCHAIR, [9.5, 0, 1.8], math.pi)        # chair
    await place(lid0, DCHAIR, [9.5, 0, 3.2], 0)              # chair opposite

    # --- Furniture: Bathroom (7,5)-(12,10) ---
    print("  Furnishing bathroom...")
    await place(lid0, TOILET, [8.5, 0, 9], math.pi)
    await place(lid0, SINK, [8.5, 0, 6])
    await place(lid0, SHOWER, [11, 0, 9])

    print("  Ground floor DONE!")

    # =================== FIRST FLOOR ===================
    print("\n--- First Floor ---")
    r = await b.cmd("create_node", node={"type":"level","level":1}, parentId=bid)
    lid1 = r.get("nodeId")
    if not lid1:
        state = await b.cmd("read_state")
        for nid, n in state.get("nodes",{}).items():
            if n.get("type")=="level" and nid != lid0: lid1 = nid; break
    print(f"  Level 1: {lid1}")
    await b.cmd("set_selection", selection={"levelId": lid1})

    await b.cmd("create_node", node={"type":"slab","polygon":[[0,0],[12,0],[12,10],[0,10]],"elevation":0.05}, parentId=lid1)

    w1 = []
    for s, e in [([0,0],[12,0]),([12,0],[12,10]),([12,10],[0,10]),([0,10],[0,0]),
                 ([0,5],[12,5]),([6,0],[6,10]),([0,7],[6,7])]:
        r = await b.cmd("create_node", node={"type":"wall","start":s,"end":e,
            "thickness":0.2 if len(w1)<4 else 0.1,"height":2.8,
            **({"frontSide":"exterior","backSide":"interior"} if len(w1)<4 else {})}, parentId=lid1)
        w1.append({"id":r.get("nodeId"),"s":s,"e":e})

    for wi, pos in [(4,3),(4,9),(5,7.5),(6,3)]:
        ww = w1[wi]
        await b.cmd("create_node", node={"type":"door","position":[wlx(ww["s"],ww["e"],pos),1.05,0],
            "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":0.8,"height":2.1}, parentId=ww["id"])

    for wi, pos in [(0,3),(0,9),(2,3),(1,7.5)]:
        ww = w1[wi]
        await b.cmd("create_node", node={"type":"window","position":[wlx(ww["s"],ww["e"],pos),1.65,0],
            "rotation":[0,0,0],"wallId":ww["id"],"side":"front","width":1.5,"height":1.5}, parentId=ww["id"])

    for nm, poly, col in [("Bedroom 1",[[0,0],[6,0],[6,5],[0,5]],"#8b5cf6"),
                           ("Bedroom 2",[[6,0],[12,0],[12,5],[6,5]],"#8b5cf6"),
                           ("Hallway",[[0,5],[6,5],[6,7],[0,7]],"#6b7280"),
                           ("Bathroom 2",[[0,7],[6,7],[6,10],[0,10]],"#06b6d4"),
                           ("Master Bedroom",[[6,5],[12,5],[12,10],[6,10]],"#a855f7")]:
        await b.cmd("create_node", node={"type":"zone","name":nm,"polygon":poly,"color":col}, parentId=lid1)

    await b.cmd("create_node", node={"type":"ceiling","polygon":[[0,0],[12,0],[12,10],[0,10]],"height":2.8}, parentId=lid1)

    # --- Furniture: Bedroom 1 (0,0)-(6,5) ---
    print("  Furnishing bedrooms...")
    await place(lid1, SBED, [1.5, 0, 1.5], math.pi/2)
    await place(lid1, BSIDE, [1.5, 0, 3])
    await place(lid1, CLOSET, [5, 0, 0.6], math.pi/2)

    # --- Furniture: Bedroom 2 (6,0)-(12,5) ---
    await place(lid1, SBED, [7.5, 0, 1.5], math.pi/2)
    await place(lid1, BSIDE, [7.5, 0, 3])
    await place(lid1, CLOSET, [11, 0, 0.6], math.pi/2)

    # --- Furniture: Master Bedroom (6,5)-(12,10) ---
    await place(lid1, DBED, [9, 0, 9], math.pi)
    await place(lid1, BSIDE, [7.5, 0, 9])
    await place(lid1, BSIDE, [10.5, 0, 9])
    await place(lid1, DRESSER, [7, 0, 6])
    await place(lid1, CLOSET, [11, 0, 5.6], math.pi/2)

    # --- Furniture: Bathroom 2 (0,7)-(6,10) ---
    print("  Furnishing bathroom 2...")
    await place(lid1, TOILET, [2, 0, 9], math.pi)
    await place(lid1, SINK, [2, 0, 7.5])
    await place(lid1, SHOWER, [5, 0, 9])

    print("  First floor DONE!")

    # =================== ROOF ===================
    print("\n--- Roof ---")
    # Position roof at center of building footprint: [6, 0, 5]
    r = await b.cmd("create_node", node={
        "type":"roof","position":[6, 0, 5],"rotation":0
    }, parentId=lid1)
    roof_id = r.get("nodeId")

    await b.cmd("create_node", node={
        "type":"roof-segment","roofType":"gable",
        "position":[0,0,0],"rotation":0,
        "width":12,"depth":10,
        "wallHeight":0.5,"roofHeight":2.5,
        "wallThickness":0.1,"deckThickness":0.1,
        "overhang":0.3,"shingleThickness":0.05
    }, parentId=roof_id)

    print("  Roof DONE!")
    print("\n" + "="*50)
    print("  COMPLETE! 2-story house with furniture")
    print("  View at http://localhost:3002")
    print("="*50)
    await b.close()

if __name__ == "__main__":
    asyncio.run(main())
