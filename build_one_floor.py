"""Presidential Residence — Grand State House with reception halls, private quarters,
offices, security features, gardens, and motorcade parking."""

import asyncio,json,math,uuid,websockets
WS="ws://localhost:3100"

class B:
    def __init__(self):self.ws=self.pending=self.listener=None
    async def connect(self):
        self.ws=await websockets.connect(WS);await self.ws.send(json.dumps({"type":"register","role":"python"}))
        self.pending={};self.listener=asyncio.create_task(self._listen());await asyncio.sleep(0.5)
    async def _listen(self):
        try:
            async for raw in self.ws:
                m=json.loads(raw);p=m.get("payload",m);mid=p.get("id")
                if mid and mid in self.pending:self.pending[mid].set_result(p)
        except:pass
    async def cmd(self,c,**kw):
        mid=uuid.uuid4().hex[:12];f=asyncio.get_running_loop().create_future();self.pending[mid]=f
        await self.ws.send(json.dumps({"type":"command","payload":{"cmd":c,"id":mid,**kw}}))
        try:r=await asyncio.wait_for(f,timeout=10)
        except asyncio.TimeoutError:return{"ok":False}
        finally:self.pending.pop(mid,None)
        data=r.get("data",r)
        if isinstance(r,dict) and r.get("ok")==False:
            err=r.get("error","unknown")
            print(f"  FATAL: {c} failed: {err}")
            raise RuntimeError(f"{c}: {err}")
        return data
    async def close(self):
        if self.listener:self.listener.cancel()
        if self.ws:await self.ws.close()
    async def log(self,msg,level="step"):
        print(f"  >> {msg}")
        await self.cmd("log",message=msg,level=level)

def X(id,cat,dims,off=None):
    return{"id":id,"category":cat,"name":id.replace("-"," ").title(),"thumbnail":"",
           "src":f"/items/{id}/model.glb","dimensions":dims,"offset":off or[0,0,0],
           "rotation":[0,0,0],"scale":[1,1,1]}

# Assets
SOFA=X("sofa","furniture",[2.5,0.8,1.5],[0,0,0.04])
LOUNGE=X("lounge-chair","furniture",[1,1.1,1.5])
LIVCHAIR=X("livingroom-chair","furniture",[1.5,0.8,1.5])
COFFEE=X("coffee-table","furniture",[2,0.4,1.5])
TVSTAND=X("tv-stand","furniture",[2,0.4,0.5],[0,0.21,0])
FLAMP=X("floor-lamp","furniture",[1,1.9,1])
DTABLE=X("dining-table","furniture",[2.5,0.8,1],[0,0,-0.01])
DCHAIR=X("dining-chair","furniture",[0.5,1,0.5])
FRIDGE=X("fridge","kitchen",[1,2,1],[0.01,0,-0.05])
STOVE=X("stove","kitchen",[1,1,1],[0,0,-0.05])
KCOUNTER=X("kitchen-counter","kitchen",[2,0.8,1])
KCABINET=X("kitchen-cabinet","kitchen",[2.5,1.1,1])
MICROWAVE=X("microwave","kitchen",[1,0.5,0.5])
STOOL=X("stool","furniture",[0.5,0.8,0.5])
DBED=X("double-bed","furniture",[2,0.8,2.5],[0,0,-0.03])
SBED=X("single-bed","furniture",[1.5,0.7,2.5])
BSIDE=X("bedside-table","furniture",[0.5,0.5,0.5],[0,0,-0.01])
CLOSET=X("closet","furniture",[2,2.5,1],[0,0,-0.01])
DRESSER=X("dresser","furniture",[1.5,0.8,1])
TLAMP=X("table-lamp","furniture",[0.5,0.5,0.5])
TOILET=X("toilet","bathroom",[1,0.9,1],[0,0,-0.23])
SINK=X("bathroom-sink","bathroom",[2,1,1.5],[0.11,0,0.02])
SHOWER=X("shower-square","bathroom",[1,2,1],[0.41,0,-0.42])
BATHTUB=X("bathtub","bathroom",[2.5,0.8,1.5])
WASHER=X("washing-machine","bathroom",[1,1,1])
OFFTABLE=X("office-table","furniture",[2,0.8,1])
OFFCHAIR=X("office-chair","furniture",[1,1.2,1])
BKSHELF=X("bookshelf","furniture",[1,2,0.5])
SHELF=X("shelf","furniture",[1,1.5,0.5])
COATRACK=X("coat-rack","furniture",[0.5,1.8,0.5])
PLANT=X("indoor-plant","furniture",[1,1.7,1])
SPLANT=X("small-indoor-plant","furniture",[0.5,0.7,0.5])
RCARPET=X("rectangular-carpet","furniture",[3,0.1,2])
RNDCARPET=X("round-carpet","furniture",[2.5,0.1,2.5])
PIANO=X("piano","furniture",[2,1.5,1])
POOLTABLE=X("pool-table","furniture",[2.5,1,4])
TREADMILL=X("threadmill","furniture",[1,1.8,1])
BARBELL=X("barbell-stand","furniture",[1.5,1,0.5])
GUITAR=X("guitar","furniture",[0.5,1,0.5])
TREE=X("tree","outdoor",[1,5,1])
FIRTREE=X("fir-tree","outdoor",[0.5,3,0.5])
PALM=X("palm","outdoor",[0.5,3.7,0.5])
BUSH=X("bush","outdoor",[3,1.1,1])
UMBRELLA=X("patio-umbrella","outdoor",[1,1.2,1.5])
SUNBED=X("sunbed","outdoor",[1.5,1.5,0.5])
HIFENCE=X("high-fence","outdoor",[2,2.5,0.5])
MEDFENCE=X("medium-fence","outdoor",[2,2,0.5])
LOFENCE=X("low-fence","outdoor",[2,0.8,0.5])
TESLA=X("tesla","outdoor",[2,1.7,5])
PARKING=X("parking-spot","outdoor",[5,1,2.5])
HOOP=X("basket-hoop","outdoor",[1,1.8,1])
PLAYHOUSE=X("outdoor-playhouse","outdoor",[0.5,0.5,1])
BALL=X("ball","outdoor",[0.5,0.3,0.5])
SCOOTER=X("scooter","outdoor",[0.5,1,0.5])
PILLAR=X("pillar","outdoor",[0.5,1.3,0.5])
COLUMN=X("column","furniture",[0.5,2.5,0.5])
STAIRS=X("stairs","furniture",[1,2.5,2])
TRASHBIN=X("trash-bin","furniture",[0.5,0.8,0.5])
MIRROR=X("round-mirror","furniture",[1,1,0.1])
PICTURE=X("picture","furniture",[1,0.7,0.1])
BOOKS=X("books","furniture",[0.5,0.3,0.3])
CACTUS=X("cactus","furniture",[0.5,0.7,0.5])

H=3.5    # grand ceiling height
H2=3.0   # upper floor height

# ============================================================================
# PRESIDENTIAL RESIDENCE — Grand State House
#
# Bird's eye layout (compound of separate volumes):
#
#     SECURITY             MOTORCADE           GUARD
#     GATEHOUSE            PARKING             HOUSE
#     [-20,-6]--[-16,-6]   [-12,-6]--[12,-6]   [16,-6]--[20,-6]
#     |  gate  |           |  6 bays  |        |  gate  |
#     [-20,-2]--[-16,-2]   [-12,-2]--[12,-2]   [16,-2]--[20,-2]
#
#                   FORMAL APPROACH / DRIVE
#             [-12,-2]===================[12,-2]
#
#     WEST WING (Offices)      MAIN BLOCK (State Rooms)      EAST WING (Private)
#     [-20,0]====[-10,0]       [0,0]================[20,0]   [24,0]=====[36,0]
#     | Chief  | Staff  |      |  RECEPTION HALL  | DINING |  | Master | Family|
#     | of Staff| Offices|      |  (grand foyer)   | HALL   |  | Suite  | Room  |
#     |--------|--------|      |  OVAL OFFICE     | STATE  |  |--------| ------|
#     | Sit.Rm | Briefing|      |  (below)         | KITCH. |  | Priv.  | Priv. |
#     [-20,12]===[-10,12]      [0,14]===============[20,14]   | Study  | Bath  |
#                                                             [24,12]====[36,12]
#
#     COVERED COLONNADE: [-10,3]--[0,7] and [20,3]--[24,7]
#
#                          SOUTH TERRACE & GARDEN
#                       [0,14]================[20,20]
#                       (covered terrace, columns, seating)
#
#                          POOL AREA
#                       [4,22]==========[16,28]
#
#     GUEST PAVILION                              STAFF QUARTERS
#     [-16,16]====[-8,24]                          [26,16]====[34,24]
#
# ============================================================================

async def p(b,pid,a,pos,rot=0,sc=None):
    await b.cmd("create_node",node={"type":"item","asset":a,"position":pos,"rotation":[0,rot,0],"scale":sc or[1,1,1]},parentId=pid)
async def W(b,pid,s,e,t=0.15,h=H,ext=False):
    nd={"type":"wall","start":s,"end":e,"thickness":t,"height":h}
    if ext:nd.update({"frontSide":"exterior","backSide":"interior"})
    r=await b.cmd("create_node",node=nd,parentId=pid)
    return{"id":r.get("nodeId"),"s":s,"e":e}
async def D(b,wo,pos,wd=0.9,ht=2.2):
    await b.cmd("create_node",node={"type":"door","position":[pos,ht/2,0],"rotation":[0,0,0],"wallId":wo["id"],"side":"front","width":wd,"height":ht},parentId=wo["id"])
async def WN(b,wo,pos,wd=2.0,ht=1.8,sl=0.8):
    await b.cmd("create_node",node={"type":"window","position":[pos,sl+ht/2,0],"rotation":[0,0,0],"wallId":wo["id"],"side":"front","width":wd,"height":ht},parentId=wo["id"])


async def main():
    b=B();await b.connect();print("[Presidential Residence] Connected\n")

    # Clear scene (no reload needed)
    print("  Clearing scene...")
    await b.cmd("clear")
    await asyncio.sleep(1)

    bid=lid0=None
    st=await b.cmd("read_state");nodes=st.get("nodes",{})
    for nid,n in nodes.items():
        if n.get("type")=="building":bid=nid
        if n.get("type")=="level":lid0=nid
    if not bid or not lid0:print("ERROR: No default scene");await b.close();return

    # Signal build start
    await b.cmd("build_start")
    L=lid0

    print("="*60)
    print("  PRESIDENTIAL RESIDENCE")
    print("="*60)
    await b.cmd("set_selection",selection={"levelId":L})

    # ==================================================================
    # A. MAIN BLOCK (0,0)-(20,14) — State Rooms
    #    Reception Hall (0,0)-(12,7), State Dining (12,0)-(20,7)
    #    Oval Office (0,7)-(10,14), State Kitchen (10,7)-(20,14)
    # ==================================================================
    await b.log("Main Block: State Rooms")

    # Slab
    await b.cmd("create_node",node={"type":"slab","polygon":[[0,0],[20,0],[20,14],[0,14]],"elevation":0.05},parentId=L)

    mw=[]
    mw.append(await W(b,L,[0,0],[20,0],0.25,H,True))      # 0: north
    mw.append(await W(b,L,[20,0],[20,14],0.25,H,True))     # 1: east
    mw.append(await W(b,L,[20,14],[0,14],0.25,H,True))     # 2: south
    mw.append(await W(b,L,[0,14],[0,0],0.25,H,True))       # 3: west

    # Interior walls
    mw.append(await W(b,L,[12,0],[12,7],0.15,H))           # 4: reception/dining divider
    mw.append(await W(b,L,[0,7],[20,7],0.15,H))            # 5: north/south divider
    mw.append(await W(b,L,[10,7],[10,14],0.15,H))          # 6: oval office/kitchen divider

    # Grand entrance (north, center of reception hall) -- double doors
    await D(b,mw[0],6,2.5,3.0)

    # Reception -> Dining door
    await D(b,mw[4],3.5,1.5,2.8)

    # Reception -> Oval Office door
    await D(b,mw[5],5,1.2,2.4)

    # Dining -> Kitchen door
    await D(b,mw[5],15,1.0,2.2)

    # Oval Office -> south terrace door
    await D(b,mw[2],5,1.5,2.4)

    # Kitchen service door (east)
    await D(b,mw[1],10,0.9,2.2)

    # Windows -- floor-to-ceiling on state rooms
    await WN(b,mw[0],2,2.8,2.4,0.3)       # reception north left
    await WN(b,mw[0],10,2.8,2.4,0.3)      # reception north right
    await WN(b,mw[0],15,2.5,2.4,0.3)      # dining north
    await WN(b,mw[3],2,2.5,2.4,0.3)       # reception west upper
    await WN(b,mw[3],5.5,2.5,2.4,0.3)     # reception west lower
    await WN(b,mw[3],10,2.5,2.4,0.3)      # oval office west
    await WN(b,mw[1],3,2.5,2.4,0.3)       # dining east
    await WN(b,mw[2],8,2.5,2.2,0.3)       # oval office south
    await WN(b,mw[2],15,2.0,2.2,0.3)      # kitchen south
    await WN(b,mw[1],12,1.0,1.0,1.2)      # kitchen east (small)

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Reception Hall","polygon":[[0,0],[12,0],[12,7],[0,7]],"color":"#d4a574"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"State Dining Hall","polygon":[[12,0],[20,0],[20,7],[12,7]],"color":"#dc2626"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Oval Office","polygon":[[0,7],[10,7],[10,14],[0,14]],"color":"#1e3a5f"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"State Kitchen","polygon":[[10,7],[20,7],[20,14],[10,14]],"color":"#f59e0b"},parentId=L)

    # Ceiling
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[0,0],[20,0],[20,14],[0,14]],"height":H},parentId=L)

    # Furnish Reception Hall
    await b.log("Furnishing: Reception Hall")
    await p(b,L,SOFA,[3,0,2.5])
    await p(b,L,SOFA,[3,0,5],math.pi)
    await p(b,L,COFFEE,[3,0,3.8])
    await p(b,L,RNDCARPET,[3,0,3.5])
    await p(b,L,LIVCHAIR,[8,0,2.5])
    await p(b,L,LIVCHAIR,[8,0,5],math.pi)
    await p(b,L,COFFEE,[8,0,3.8])
    await p(b,L,FLAMP,[0.8,0,0.8])
    await p(b,L,FLAMP,[11,0,0.8])
    await p(b,L,PLANT,[11,0,6])
    await p(b,L,PLANT,[0.8,0,6])
    await p(b,L,COATRACK,[1,0,0.5])
    await p(b,L,RCARPET,[6,0,3.5])
    await p(b,L,PIANO,[9,0,6],math.pi/2)

    # Furnish State Dining Hall
    await b.log("Furnishing: State Dining Hall")
    # Long banquet table with 10 chairs
    await p(b,L,DTABLE,[16,0,2.5])
    await p(b,L,DTABLE,[16,0,4.5])
    for tz in [1.8,3.2,4.5,5.5]:
        await p(b,L,DCHAIR,[14.8,0,tz],math.pi/2)
        await p(b,L,DCHAIR,[17.2,0,tz],-math.pi/2)
    await p(b,L,DCHAIR,[16,0,1.2],math.pi)
    await p(b,L,DCHAIR,[16,0,6.2])
    await p(b,L,PLANT,[13,0,0.5])
    await p(b,L,PLANT,[19,0,0.5])
    await p(b,L,FLAMP,[13,0,6])
    await p(b,L,FLAMP,[19,0,6])

    # Furnish Oval Office
    await b.log("Furnishing: Oval Office")
    await p(b,L,OFFTABLE,[5,0,10])
    await p(b,L,OFFCHAIR,[5,0,10.8])
    await p(b,L,LIVCHAIR,[3,0,8.5],math.pi/4)
    await p(b,L,LIVCHAIR,[7,0,8.5],-math.pi/4)
    await p(b,L,SOFA,[5,0,8])
    await p(b,L,COFFEE,[5,0,9])
    await p(b,L,RNDCARPET,[5,0,10])
    await p(b,L,BKSHELF,[1,0,7.5])
    await p(b,L,BKSHELF,[1,0,9])
    await p(b,L,BKSHELF,[1,0,10.5])
    await p(b,L,PLANT,[9,0,7.5])
    await p(b,L,PLANT,[0.5,0,13])
    await p(b,L,BOOKS,[6.5,0,10.2])
    await p(b,L,PICTURE,[5,0,7.3])
    await p(b,L,FLAMP,[9,0,13])

    # Furnish State Kitchen
    await b.log("Furnishing: State Kitchen")
    await p(b,L,KCOUNTER,[12,0,8.5])
    await p(b,L,KCOUNTER,[14,0,8.5])
    await p(b,L,KCOUNTER,[16,0,8.5])
    await p(b,L,FRIDGE,[19,0,8],math.pi)
    await p(b,L,STOVE,[18,0,13],math.pi)
    await p(b,L,STOVE,[16,0,13],math.pi)
    await p(b,L,KCABINET,[12,0,13.2],math.pi)
    await p(b,L,KCABINET,[14.5,0,13.2],math.pi)
    await p(b,L,MICROWAVE,[19,0,10])
    await p(b,L,TRASHBIN,[11,0,13])

    # ==================================================================
    # B. WEST WING (-20,0)-(-10,12) — Offices & Situation Room
    #    Chief of Staff (-20,0)-(-15,6), Staff Offices (-15,0)-(-10,6)
    #    Situation Room (-20,6)-(-15,12), Briefing Room (-15,6)-(-10,12)
    # ==================================================================
    await b.log("West Wing: Offices & Situation Room")

    await b.cmd("create_node",node={"type":"slab","polygon":[[-20,0],[-10,0],[-10,12],[-20,12]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-20,0],[-10,0],[-10,12],[-20,12]],"height":H},parentId=L)

    ww=[]
    ww.append(await W(b,L,[-20,0],[-10,0],0.2,H,True))     # 0: north
    ww.append(await W(b,L,[-10,0],[-10,12],0.2,H,True))     # 1: east
    ww.append(await W(b,L,[-10,12],[-20,12],0.2,H,True))    # 2: south
    ww.append(await W(b,L,[-20,12],[-20,0],0.2,H,True))     # 3: west

    # Interior dividers
    ww.append(await W(b,L,[-15,0],[-15,12],0.12,H))         # 4: vertical center
    ww.append(await W(b,L,[-20,6],[-10,6],0.12,H))          # 5: horizontal center

    # Doors
    await D(b,ww[1],3,1.0,2.2)      # staff offices -> colonnade
    await D(b,ww[1],9,1.0,2.2)      # briefing room -> colonnade
    await D(b,ww[4],3,0.9,2.2)      # chief of staff -> staff offices
    await D(b,ww[5],2.5,0.9,2.2)    # chief of staff -> situation room
    await D(b,ww[5],7.5,0.9,2.2)    # staff offices -> briefing room
    await D(b,ww[4],9,0.9,2.2)      # situation room -> briefing room

    # Windows
    await WN(b,ww[0],2.5,2.0,2.0,0.3)    # chief of staff north
    await WN(b,ww[0],7.5,2.0,2.0,0.3)    # staff offices north
    await WN(b,ww[3],3,2.0,2.0,0.3)      # chief of staff west
    await WN(b,ww[3],9,2.0,2.0,0.3)      # situation room west
    await WN(b,ww[2],2.5,1.5,1.5,0.5)    # situation room south (smaller, security)
    await WN(b,ww[2],7.5,1.5,1.5,0.5)    # briefing room south

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Chief of Staff Office","polygon":[[-20,0],[-15,0],[-15,6],[-20,6]],"color":"#2563eb"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Staff Offices","polygon":[[-15,0],[-10,0],[-10,6],[-15,6]],"color":"#3b82f6"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Situation Room","polygon":[[-20,6],[-15,6],[-15,12],[-20,12]],"color":"#991b1b"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Press Briefing Room","polygon":[[-15,6],[-10,6],[-10,12],[-15,12]],"color":"#6366f1"},parentId=L)

    # Furnish Chief of Staff Office
    await b.log("Furnishing: West Wing Offices")
    await p(b,L,OFFTABLE,[-17.5,0,3])
    await p(b,L,OFFCHAIR,[-17.5,0,3.8])
    await p(b,L,BKSHELF,[-19.5,0,0.5])
    await p(b,L,BKSHELF,[-19.5,0,2])
    await p(b,L,LIVCHAIR,[-17,0,1],math.pi/4)
    await p(b,L,PLANT,[-15.5,0,5.5])
    await p(b,L,BOOKS,[-16,0,3.2])

    # Furnish Staff Offices (3 desks)
    await p(b,L,OFFTABLE,[-13,0,1.5])
    await p(b,L,OFFCHAIR,[-13,0,2.3])
    await p(b,L,OFFTABLE,[-13,0,4])
    await p(b,L,OFFCHAIR,[-13,0,4.8])
    await p(b,L,SHELF,[-10.5,0,0.5])
    await p(b,L,SHELF,[-10.5,0,2])
    await p(b,L,TRASHBIN,[-11,0,5])

    # Furnish Situation Room (conference table, screens)
    await p(b,L,DTABLE,[-17.5,0,9])
    await p(b,L,OFFCHAIR,[-17.5,0,8],math.pi)
    await p(b,L,OFFCHAIR,[-17.5,0,10])
    await p(b,L,OFFCHAIR,[-18.7,0,9],math.pi/2)
    await p(b,L,OFFCHAIR,[-16.3,0,9],-math.pi/2)
    await p(b,L,OFFCHAIR,[-18.7,0,8],math.pi/2)
    await p(b,L,OFFCHAIR,[-16.3,0,8],-math.pi/2)
    await p(b,L,TVSTAND,[-19.5,0,7])
    await p(b,L,BKSHELF,[-19.5,0,11])

    # Furnish Press Briefing Room (podium area + seating)
    await p(b,L,KCOUNTER,[-12.5,0,7])     # podium (counter as lectern)
    await p(b,L,DCHAIR,[-13,0,8.5])
    await p(b,L,DCHAIR,[-12,0,8.5])
    await p(b,L,DCHAIR,[-13,0,9.5])
    await p(b,L,DCHAIR,[-12,0,9.5])
    await p(b,L,DCHAIR,[-13,0,10.5])
    await p(b,L,DCHAIR,[-12,0,10.5])
    await p(b,L,PLANT,[-10.5,0,6.5])

    # ==================================================================
    # C. EAST WING (24,0)-(36,12) — Private Quarters
    #    Master Suite (24,0)-(30,6), Family Room (30,0)-(36,6)
    #    Private Study (24,6)-(30,12), Master Bath (30,6)-(36,12)
    # ==================================================================
    await b.log("East Wing: Private Quarters")

    await b.cmd("create_node",node={"type":"slab","polygon":[[24,0],[36,0],[36,12],[24,12]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[24,0],[36,0],[36,12],[24,12]],"height":H},parentId=L)

    ew=[]
    ew.append(await W(b,L,[24,0],[36,0],0.2,H,True))      # 0: north
    ew.append(await W(b,L,[36,0],[36,12],0.2,H,True))      # 1: east
    ew.append(await W(b,L,[36,12],[24,12],0.2,H,True))     # 2: south
    ew.append(await W(b,L,[24,12],[24,0],0.2,H,True))      # 3: west

    # Interior dividers
    ew.append(await W(b,L,[30,0],[30,12],0.12,H))          # 4: vertical center
    ew.append(await W(b,L,[24,6],[36,6],0.12,H))           # 5: horizontal center

    # Doors
    await D(b,ew[3],3,1.0,2.2)      # master suite -> colonnade
    await D(b,ew[3],9,1.0,2.2)      # private study -> colonnade
    await D(b,ew[4],3,0.9,2.2)      # master suite -> family room
    await D(b,ew[5],3,0.9,2.2)      # master suite -> private study
    await D(b,ew[5],9,0.9,2.2)      # family room -> master bath
    await D(b,ew[4],9,0.9,2.2)      # study -> bath

    # Windows -- generous windows for private quarters
    await WN(b,ew[0],3,2.5,2.2,0.3)     # master suite north
    await WN(b,ew[0],9,2.5,2.2,0.3)     # family room north
    await WN(b,ew[1],3,2.5,2.2,0.3)     # family room east
    await WN(b,ew[1],9,2.5,2.2,0.3)     # master bath east
    await WN(b,ew[2],3,2.5,2.2,0.3)     # private study south
    await WN(b,ew[2],9,1.0,1.0,1.2)     # master bath south (small)

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Master Suite","polygon":[[24,0],[30,0],[30,6],[24,6]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Family Room","polygon":[[30,0],[36,0],[36,6],[30,6]],"color":"#ec4899"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Private Study","polygon":[[24,6],[30,6],[30,12],[24,12]],"color":"#059669"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Master Bath","polygon":[[30,6],[36,6],[36,12],[30,12]],"color":"#06b6d4"},parentId=L)

    # Furnish Master Suite
    await b.log("Furnishing: Private Quarters")
    await p(b,L,DBED,[27,0,3])
    await p(b,L,BSIDE,[25,0,2.5])
    await p(b,L,BSIDE,[29,0,2.5])
    await p(b,L,TLAMP,[25,0,2.5])
    await p(b,L,TLAMP,[29,0,2.5])
    await p(b,L,CLOSET,[27,0,5.5],math.pi)
    await p(b,L,DRESSER,[25,0,5],math.pi/2)
    await p(b,L,RCARPET,[27,0,3])
    await p(b,L,FLAMP,[24.5,0,0.5])
    await p(b,L,SPLANT,[29.5,0,0.5])

    # Furnish Family Room
    await p(b,L,SOFA,[33,0,2])
    await p(b,L,SOFA,[33,0,4.5],math.pi)
    await p(b,L,COFFEE,[33,0,3.2])
    await p(b,L,TVSTAND,[35,0,3],math.pi/2)
    await p(b,L,RNDCARPET,[33,0,3])
    await p(b,L,BKSHELF,[30.5,0,0.5])
    await p(b,L,PLANT,[35,0,0.5])
    await p(b,L,PLANT,[35,0,5.5])

    # Furnish Private Study
    await p(b,L,OFFTABLE,[27,0,9])
    await p(b,L,OFFCHAIR,[27,0,9.8])
    await p(b,L,BKSHELF,[24.5,0,7])
    await p(b,L,BKSHELF,[24.5,0,8.5])
    await p(b,L,BKSHELF,[24.5,0,10])
    await p(b,L,LIVCHAIR,[28,0,7.5],math.pi/4)
    await p(b,L,GUITAR,[29,0,11])
    await p(b,L,SPLANT,[29,0,7])
    await p(b,L,FLAMP,[24.5,0,11.5])
    await p(b,L,BOOKS,[27.5,0,9.2])

    # Furnish Master Bath
    await p(b,L,BATHTUB,[33,0,7.5])
    await p(b,L,SHOWER,[35,0,7.5])
    await p(b,L,TOILET,[31,0,10],math.pi)
    await p(b,L,SINK,[33,0,10])
    await p(b,L,MIRROR,[33,0,6.5])
    await p(b,L,WASHER,[35,0,11])
    await p(b,L,SPLANT,[31,0,7])

    # ==================================================================
    # D. COVERED COLONNADES — connecting wings to main block
    # ==================================================================
    await b.log("Covered Colonnades")

    # West colonnade: (-10,2)-(0,6)
    await b.cmd("create_node",node={"type":"slab","polygon":[[-10,2],[0,2],[0,6],[-10,6]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-10,2],[0,2],[0,6],[-10,6]],"height":H},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"West Colonnade","polygon":[[-10,2],[0,2],[0,6],[-10,6]],"color":"#9ca3af"},parentId=L)
    for cx in [-9,-7,-5,-3,-1]:
        await p(b,L,PILLAR,[cx,0,2.3],0,[1,2.5,1])
        await p(b,L,PILLAR,[cx,0,5.7],0,[1,2.5,1])
    await p(b,L,PLANT,[-5,0,4])
    await p(b,L,SPLANT,[-2,0,4])

    # East colonnade: (20,2)-(24,6)
    await b.cmd("create_node",node={"type":"slab","polygon":[[20,2],[24,2],[24,6],[20,6]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[20,2],[24,2],[24,6],[20,6]],"height":H},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"East Colonnade","polygon":[[20,2],[24,2],[24,6],[20,6]],"color":"#9ca3af"},parentId=L)
    await p(b,L,PILLAR,[20.3,0,2.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[20.3,0,5.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[22,0,2.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[22,0,5.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[23.7,0,2.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[23.7,0,5.7],0,[1,2.5,1])
    await p(b,L,PLANT,[22,0,4])

    # ==================================================================
    # E. SOUTH TERRACE (0,14)-(20,20) — Covered terrace with garden views
    # ==================================================================
    await b.log("South Terrace & Gardens")

    await b.cmd("create_node",node={"type":"slab","polygon":[[0,14],[20,14],[20,20],[0,20]],"elevation":0.03},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[2,14],[18,14],[18,18],[2,18]],"height":H},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"South Terrace","polygon":[[0,14],[20,14],[20,20],[0,20]],"color":"#a3e635"},parentId=L)

    # Terrace columns (covered area 2-18, 14-18)
    for cx in [2,5,8,11,14,17]:
        await p(b,L,PILLAR,[cx,0,14.3],0,[1,2.5,1])
        await p(b,L,PILLAR,[cx,0,17.7],0,[1,2.5,1])

    # Terrace furniture
    await p(b,L,UMBRELLA,[4,0,16])
    await p(b,L,DTABLE,[4,0,16])
    await p(b,L,DCHAIR,[4,0,15.2],math.pi)
    await p(b,L,DCHAIR,[4,0,16.8])
    await p(b,L,DCHAIR,[2.8,0,16],math.pi/2)
    await p(b,L,DCHAIR,[5.2,0,16],-math.pi/2)

    await p(b,L,UMBRELLA,[10,0,16])
    await p(b,L,SOFA,[10,0,15.5])
    await p(b,L,LOUNGE,[10,0,17],math.pi)
    await p(b,L,COFFEE,[10,0,16.3])

    await p(b,L,UMBRELLA,[16,0,16])
    await p(b,L,DTABLE,[16,0,16])
    await p(b,L,DCHAIR,[16,0,15.2],math.pi)
    await p(b,L,DCHAIR,[16,0,16.8])
    await p(b,L,DCHAIR,[14.8,0,16],math.pi/2)
    await p(b,L,DCHAIR,[17.2,0,16],-math.pi/2)

    # Open terrace seating (south part, uncovered)
    await p(b,L,SUNBED,[4,0,19],math.pi/2)
    await p(b,L,SUNBED,[8,0,19],math.pi/2)
    await p(b,L,SUNBED,[12,0,19],math.pi/2)
    await p(b,L,SUNBED,[16,0,19],math.pi/2)

    # ==================================================================
    # F. SWIMMING POOL (4,22)-(16,28) — south of terrace
    # ==================================================================
    await b.log("Swimming Pool & Deck")

    # Pool slab (sunken)
    await b.cmd("create_node",node={"type":"slab","polygon":[[5,22],[15,22],[15,27],[5,27]],"elevation":-0.5},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Presidential Pool","polygon":[[5,22],[15,22],[15,27],[5,27]],"color":"#0284c7"},parentId=L)

    # Pool deck
    await b.cmd("create_node",node={"type":"slab","polygon":[[2,20],[18,20],[18,29],[2,29]],"elevation":0.02,
        "holes":[[[5,22],[15,22],[15,27],[5,27]]]},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Pool Deck","polygon":[[2,20],[18,20],[18,29],[2,29]],"color":"#d4a574"},parentId=L)

    # Pool furniture
    await p(b,L,SUNBED,[3,0,23],math.pi/2)
    await p(b,L,SUNBED,[3,0,25],math.pi/2)
    await p(b,L,UMBRELLA,[3,0,24])
    await p(b,L,SUNBED,[17,0,23],-math.pi/2)
    await p(b,L,SUNBED,[17,0,25],-math.pi/2)
    await p(b,L,UMBRELLA,[17,0,24])
    await p(b,L,SUNBED,[8,0,28])
    await p(b,L,SUNBED,[10,0,28])
    await p(b,L,SUNBED,[12,0,28])
    await p(b,L,UMBRELLA,[10,0,28.5])

    # ==================================================================
    # G. GUEST PAVILION (-16,16)-(-8,24) — Separate building
    # ==================================================================
    await b.log("Guest Pavilion")

    await b.cmd("create_node",node={"type":"slab","polygon":[[-16,16],[-8,16],[-8,24],[-16,24]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-16,16],[-8,16],[-8,24],[-16,24]],"height":3.2},parentId=L)

    gw=[]
    gw.append(await W(b,L,[-16,16],[-8,16],0.2,3.2,True))    # 0: north
    gw.append(await W(b,L,[-8,16],[-8,24],0.2,3.2,True))     # 1: east
    gw.append(await W(b,L,[-8,24],[-16,24],0.2,3.2,True))    # 2: south
    gw.append(await W(b,L,[-16,24],[-16,16],0.2,3.2,True))   # 3: west

    # Interior wall dividing into 2 guest suites
    gw.append(await W(b,L,[-12,16],[-12,24],0.12,3.2))       # 4: center divider
    # Bath walls for each suite
    gw.append(await W(b,L,[-16,21],[-12,21],0.1,3.2))        # 5: suite 1 bath wall
    gw.append(await W(b,L,[-12,21],[-8,21],0.1,3.2))         # 6: suite 2 bath wall

    # Doors -- entrance from north
    await D(b,gw[0],2,1.0,2.2)    # suite 1 entrance
    await D(b,gw[0],6,1.0,2.2)    # suite 2 entrance
    # Bath doors
    await D(b,gw[5],2,0.7,2.1)    # suite 1 bath
    await D(b,gw[6],2,0.7,2.1)    # suite 2 bath

    # Windows
    await WN(b,gw[3],4,1.8,1.8,0.5)     # suite 1 west
    await WN(b,gw[1],4,1.8,1.8,0.5)     # suite 2 east
    await WN(b,gw[2],2,1.0,1.0,1.2)     # suite 1 bath south
    await WN(b,gw[2],6,1.0,1.0,1.2)     # suite 2 bath south

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Guest Suite 1","polygon":[[-16,16],[-12,16],[-12,21],[-16,21]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Guest Bath 1","polygon":[[-16,21],[-12,21],[-12,24],[-16,24]],"color":"#06b6d4"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Guest Suite 2","polygon":[[-12,16],[-8,16],[-8,21],[-12,21]],"color":"#8b5cf6"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Guest Bath 2","polygon":[[-12,21],[-8,21],[-8,24],[-12,24]],"color":"#0891b2"},parentId=L)

    # Furnish Guest Suite 1
    await b.log("Furnishing: Guest Pavilion")
    await p(b,L,DBED,[-14,0,18.5])
    await p(b,L,BSIDE,[-15.5,0,18])
    await p(b,L,BSIDE,[-12.5,0,18])
    await p(b,L,CLOSET,[-14,0,20.5],math.pi)
    await p(b,L,DRESSER,[-15.5,0,16.5])
    await p(b,L,RCARPET,[-14,0,18.5])
    # Bath 1
    await p(b,L,SHOWER,[-15,0,22])
    await p(b,L,TOILET,[-13,0,23],math.pi)
    await p(b,L,SINK,[-14,0,21.5])

    # Furnish Guest Suite 2
    await p(b,L,DBED,[-10,0,18.5])
    await p(b,L,BSIDE,[-11.5,0,18])
    await p(b,L,BSIDE,[-8.5,0,18])
    await p(b,L,CLOSET,[-10,0,20.5],math.pi)
    await p(b,L,DRESSER,[-8.5,0,16.5],math.pi)
    await p(b,L,RCARPET,[-10,0,18.5])
    # Bath 2
    await p(b,L,SHOWER,[-11,0,22])
    await p(b,L,TOILET,[-9,0,23],math.pi)
    await p(b,L,SINK,[-10,0,21.5])

    # ==================================================================
    # H. STAFF QUARTERS (26,16)-(34,24) — Separate building
    # ==================================================================
    await b.log("Staff Quarters")

    await b.cmd("create_node",node={"type":"slab","polygon":[[26,16],[34,16],[34,24],[26,24]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[26,16],[34,16],[34,24],[26,24]],"height":3.0},parentId=L)

    sw=[]
    sw.append(await W(b,L,[26,16],[34,16],0.2,3.0,True))     # 0: north
    sw.append(await W(b,L,[34,16],[34,24],0.2,3.0,True))     # 1: east
    sw.append(await W(b,L,[34,24],[26,24],0.2,3.0,True))     # 2: south
    sw.append(await W(b,L,[26,24],[26,16],0.2,3.0,True))     # 3: west

    # Interior: 4 staff rooms (2x2 grid)
    sw.append(await W(b,L,[30,16],[30,24],0.12,3.0))         # 4: vertical center
    sw.append(await W(b,L,[26,20],[34,20],0.12,3.0))         # 5: horizontal center

    # Doors -- entrance from west
    await D(b,sw[3],2,0.9,2.2)      # room 1
    await D(b,sw[3],6,0.9,2.2)      # room 3
    # Doors from east
    await D(b,sw[1],2,0.9,2.2)      # room 2
    await D(b,sw[1],6,0.9,2.2)      # room 4

    # Windows
    await WN(b,sw[0],2,1.5,1.5,0.5)    # room 1 north
    await WN(b,sw[0],6,1.5,1.5,0.5)    # room 2 north
    await WN(b,sw[2],2,1.5,1.5,0.5)    # room 3 south
    await WN(b,sw[2],6,1.5,1.5,0.5)    # room 4 south

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Staff Room 1","polygon":[[26,16],[30,16],[30,20],[26,20]],"color":"#6b7280"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Staff Room 2","polygon":[[30,16],[34,16],[34,20],[30,20]],"color":"#9ca3af"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Staff Room 3","polygon":[[26,20],[30,20],[30,24],[26,24]],"color":"#6b7280"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Staff Room 4","polygon":[[30,20],[34,20],[34,24],[30,24]],"color":"#9ca3af"},parentId=L)

    # Furnish staff rooms
    await b.log("Furnishing: Staff Quarters")
    for sx,sz in [(28,18),(32,18),(28,22),(32,22)]:
        await p(b,L,SBED,[sx,0,sz])
        await p(b,L,BSIDE,[sx-1.2,0,sz-0.5])
        await p(b,L,DRESSER,[sx+1,0,sz+1],math.pi)
        await p(b,L,SHELF,[sx-1.5,0,sz+1.5])

    # ==================================================================
    # I. MOTORCADE PARKING (-12,-6)-(12,-2) — Secure covered parking
    # ==================================================================
    await b.log("Motorcade Parking")

    await b.cmd("create_node",node={"type":"slab","polygon":[[-12,-6],[12,-6],[12,-2],[-12,-2]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Motorcade Parking","polygon":[[-12,-6],[12,-6],[12,-2],[-12,-2]],"color":"#44403c"},parentId=L)

    # Carport ceiling
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-12,-6],[12,-6],[12,-2],[-12,-2]],"height":3.0},parentId=L)

    # Carport columns
    for cx in [-11,-7,-3,1,5,9]:
        await p(b,L,PILLAR,[cx,0,-5.7],0,[1,2.1,1])
        await p(b,L,PILLAR,[cx,0,-2.3],0,[1,2.1,1])

    # Motorcade vehicles (6 Teslas as presidential fleet)
    await p(b,L,TESLA,[-9,0,-4],math.pi/2)
    await p(b,L,TESLA,[-5,0,-4],math.pi/2)
    await p(b,L,TESLA,[-1,0,-4],math.pi/2)
    await p(b,L,TESLA,[3,0,-4],math.pi/2)
    await p(b,L,TESLA,[7,0,-4],math.pi/2)
    await p(b,L,TESLA,[11,0,-4],math.pi/2)

    # ==================================================================
    # J. SECURITY GATEHOUSES
    # ==================================================================
    await b.log("Security Gatehouses")

    # West Gatehouse (-20,-6)-(-16,-2)
    await b.cmd("create_node",node={"type":"slab","polygon":[[-20,-6],[-16,-6],[-16,-2],[-20,-2]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-20,-6],[-16,-6],[-16,-2],[-20,-2]],"height":2.8},parentId=L)

    sg1=[]
    sg1.append(await W(b,L,[-20,-6],[-16,-6],0.15,2.8,True))  # 0: north
    sg1.append(await W(b,L,[-16,-6],[-16,-2],0.15,2.8,True))  # 1: east
    sg1.append(await W(b,L,[-16,-2],[-20,-2],0.15,2.8,True))  # 2: south
    sg1.append(await W(b,L,[-20,-2],[-20,-6],0.15,2.8,True))  # 3: west

    await D(b,sg1[1],2,0.9,2.2)   # gate exit
    await D(b,sg1[2],2,0.9,2.2)   # south access
    await WN(b,sg1[0],2,1.5,1.2,0.8)
    await WN(b,sg1[3],2,1.2,1.2,0.8)

    await b.cmd("create_node",node={"type":"zone","name":"West Gatehouse","polygon":[[-20,-6],[-16,-6],[-16,-2],[-20,-2]],"color":"#374151"},parentId=L)

    # Gatehouse furniture
    await p(b,L,OFFTABLE,[-18,0,-4])
    await p(b,L,OFFCHAIR,[-18,0,-3.2])
    await p(b,L,SHELF,[-19.5,0,-5])

    # East Gatehouse (16,-6)-(20,-2)
    await b.cmd("create_node",node={"type":"slab","polygon":[[16,-6],[20,-6],[20,-2],[16,-2]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[16,-6],[20,-6],[20,-2],[16,-2]],"height":2.8},parentId=L)

    sg2=[]
    sg2.append(await W(b,L,[16,-6],[20,-6],0.15,2.8,True))  # 0: north
    sg2.append(await W(b,L,[20,-6],[20,-2],0.15,2.8,True))  # 1: east
    sg2.append(await W(b,L,[20,-2],[16,-2],0.15,2.8,True))  # 2: south
    sg2.append(await W(b,L,[16,-2],[16,-6],0.15,2.8,True))  # 3: west

    await D(b,sg2[3],2,0.9,2.2)   # gate entry
    await D(b,sg2[2],2,0.9,2.2)   # south access
    await WN(b,sg2[0],2,1.5,1.2,0.8)
    await WN(b,sg2[1],2,1.2,1.2,0.8)

    await b.cmd("create_node",node={"type":"zone","name":"East Gatehouse","polygon":[[16,-6],[20,-6],[20,-2],[16,-2]],"color":"#374151"},parentId=L)

    await p(b,L,OFFTABLE,[18,0,-4])
    await p(b,L,OFFCHAIR,[18,0,-3.2])
    await p(b,L,SHELF,[16.5,0,-5])

    # ==================================================================
    # K. FORMAL APPROACH / DRIVE (-12,-2)-(12,0) — Grand approach slab
    # ==================================================================
    await b.log("Formal Approach Drive")

    await b.cmd("create_node",node={"type":"slab","polygon":[[-12,-2],[12,-2],[12,0],[-12,0]],"elevation":0.03},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Formal Drive","polygon":[[-12,-2],[12,-2],[12,0],[-12,0]],"color":"#d4a574"},parentId=L)

    # Approach columns (ceremonial)
    for cx in [-10,-6,-2,2,6,10]:
        await p(b,L,PILLAR,[cx,0,-0.3],0,[1,2.5,1])

    # ==================================================================
    # L. ROSE GARDEN — between guest pavilion and pool
    # ==================================================================
    await b.log("Rose Garden & Landscaping")

    await b.cmd("create_node",node={"type":"slab","polygon":[[-6,20],[2,20],[2,28],[-6,28]],"elevation":0.01},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Rose Garden","polygon":[[-6,20],[2,20],[2,28],[-6,28]],"color":"#16a34a"},parentId=L)

    # Rose garden features
    await p(b,L,PALM,[-4,0,22])
    await p(b,L,PALM,[-2,0,25])
    await p(b,L,PALM,[0,0,22])
    await p(b,L,BUSH,[-5,0,23])
    await p(b,L,BUSH,[-3,0,26])
    await p(b,L,BUSH,[-1,0,23])
    await p(b,L,BUSH,[1,0,26])
    await p(b,L,UMBRELLA,[-2,0,24])
    await p(b,L,DCHAIR,[-3,0,24],math.pi/2)
    await p(b,L,DCHAIR,[-1,0,24],-math.pi/2)

    # ==================================================================
    # M. PERIMETER LANDSCAPE — Trees, hedges, security fencing
    # ==================================================================
    await b.log("Perimeter Security & Landscape")

    # High fence around property perimeter
    # North perimeter fencing
    for fx in range(-20,36,4):
        await p(b,L,HIFENCE,[fx,0,-8])

    # South perimeter fencing
    for fx in range(-20,36,4):
        await p(b,L,HIFENCE,[fx,0,30])

    # West perimeter fencing
    for fz in range(-8,30,4):
        await p(b,L,HIFENCE,[-22,0,fz],math.pi/2)

    # East perimeter fencing
    for fz in range(-8,30,4):
        await p(b,L,HIFENCE,[38,0,fz],math.pi/2)

    # Perimeter trees (privacy screening)
    for tx in range(-18,36,6):
        await p(b,L,TREE,[tx,0,-7])
        await p(b,L,TREE,[tx,0,29])
    for tz in range(-6,28,6):
        await p(b,L,TREE,[-21,0,tz])
        await p(b,L,TREE,[37,0,tz])

    # Fir trees (dense privacy screening near gatehouses)
    for fz in [-7,-5,-3]:
        await p(b,L,FIRTREE,[-21,0,fz])
        await p(b,L,FIRTREE,[21,0,fz])

    # Palm avenue along formal drive
    for cx in [-10,-6,-2,2,6,10]:
        await p(b,L,PALM,[cx,0,-1])

    # Garden bushes around main block
    for bx in range(1,19,3):
        await p(b,L,BUSH,[bx,0,-0.5])
    for bx in range(1,19,3):
        await p(b,L,BUSH,[bx,0,14.5])

    # Garden between west wing and guest pavilion
    await p(b,L,BUSH,[-18,0,14])
    await p(b,L,BUSH,[-14,0,14])
    await p(b,L,BUSH,[-10,0,14])
    await p(b,L,PALM,[-20,0,15])
    await p(b,L,PALM,[-8,0,14])

    # Garden between east wing and staff quarters
    await p(b,L,BUSH,[36,0,14])
    await p(b,L,BUSH,[32,0,14])
    await p(b,L,BUSH,[28,0,14])
    await p(b,L,PALM,[36,0,15])
    await p(b,L,PALM,[24,0,14])

    # Courtyard garden between south terrace and pool
    await p(b,L,PALM,[1,0,21])
    await p(b,L,PALM,[19,0,21])
    await p(b,L,BUSH,[5,0,20.5])
    await p(b,L,BUSH,[10,0,20.5])
    await p(b,L,BUSH,[15,0,20.5])

    # ==================================================================
    # N. BASKETBALL COURT (east garden area)
    # ==================================================================
    await b.log("Recreation: Basketball Court")

    await b.cmd("create_node",node={"type":"slab","polygon":[[26,26],[34,26],[34,30],[26,30]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Basketball Court","polygon":[[26,26],[34,26],[34,30],[26,30]],"color":"#ea580c"},parentId=L)
    await p(b,L,HOOP,[30,0,26.5])
    await p(b,L,HOOP,[30,0,29.5],math.pi)
    await p(b,L,BALL,[31,0,28])

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print(f"\n{'='*60}")
    print("  PRESIDENTIAL RESIDENCE -- COMPLETE")
    print("  " + "-"*44)
    print("  MAIN BLOCK (20x14m):")
    print("    Reception Hall (12x7m) -- grand foyer with piano")
    print("    State Dining Hall (8x7m) -- banquet for 12")
    print("    Oval Office (10x7m) -- presidential desk, bookshelves")
    print("    State Kitchen (10x7m) -- commercial-grade")
    print("")
    print("  WEST WING (10x12m) -- Executive Offices:")
    print("    Chief of Staff Office")
    print("    Staff Offices (3 desks)")
    print("    Situation Room (conference for 8)")
    print("    Press Briefing Room")
    print("")
    print("  EAST WING (12x12m) -- Private Quarters:")
    print("    Master Suite with king bed")
    print("    Family Room with sofas and TV")
    print("    Private Study with bookshelves")
    print("    Master Bath (bathtub, shower, double sink)")
    print("")
    print("  GUEST PAVILION (8x8m):")
    print("    2 guest suites with en-suite bathrooms")
    print("")
    print("  STAFF QUARTERS (8x8m):")
    print("    4 staff rooms with single beds")
    print("")
    print("  SECURITY:")
    print("    2 gatehouses (west and east)")
    print("    Motorcade parking (6 vehicles)")
    print("    High-fence perimeter security")
    print("")
    print("  OUTDOOR:")
    print("    Covered colonnades (west and east)")
    print("    South terrace with dining and seating")
    print("    Presidential pool (10x5m) with deck")
    print("    Rose garden with palms")
    print("    Basketball court")
    print("    Formal approach drive with palm avenue")
    print("    Perimeter trees and privacy hedges")
    print("  " + "-"*44)
    print("  COMPOUND: 7 separate volumes")
    print("  STYLE: Grand state house, 3.5m ceilings")
    print(f"{'='*60}")

    # Signal build complete
    await b.cmd("build_end")
    print("\n  Build complete.")
    await b.close()

if __name__=="__main__":
    asyncio.run(main())
