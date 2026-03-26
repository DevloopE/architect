"""Modern Compound Estate — separate volumes, pool, outdoor living, negative space."""

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
        return r.get("data",r)
    async def close(self):
        if self.listener:self.listener.cancel()
        if self.ws:await self.ws.close()

def X(id,cat,dims,off=None):
    return{"id":id,"category":cat,"name":id.replace("-"," ").title(),"thumbnail":"",
           "src":f"/items/{id}/model.glb","dimensions":dims,"offset":off or[0,0,0],
           "rotation":[0,0,0],"scale":[1,1,1]}

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
DBED=X("double-bed","furniture",[2,0.8,2.5],[0,0,-0.03])
SBED=X("single-bed","furniture",[1.5,0.7,2.5])
BSIDE=X("bedside-table","furniture",[0.5,0.5,0.5],[0,0,-0.01])
CLOSET=X("closet","furniture",[2,2.5,1],[0,0,-0.01])
DRESSER=X("dresser","furniture",[1.5,0.8,1])
TOILET=X("toilet","bathroom",[1,0.9,1],[0,0,-0.23])
SINK=X("bathroom-sink","bathroom",[2,1,1.5],[0.11,0,0.02])
SHOWER=X("shower-square","bathroom",[1,2,1],[0.41,0,-0.42])
BATHTUB=X("bathtub","bathroom",[2.5,0.8,1.5])
OFFTABLE=X("office-table","furniture",[2,0.8,1])
OFFCHAIR=X("office-chair","furniture",[1,1.2,1])
BKSHELF=X("bookshelf","furniture",[1,2,0.5])
COATRACK=X("coat-rack","furniture",[0.5,1.8,0.5])
PLANT=X("indoor-plant","furniture",[1,1.7,1])
SPLANT=X("small-indoor-plant","furniture",[0.5,0.7,0.5])
RCARPET=X("rectangular-carpet","furniture",[3,0.1,2])
RNDCARPET=X("round-carpet","furniture",[2.5,0.1,2.5])
PIANO=X("piano","furniture",[2,1.5,1])
POOLTABLE=X("pool-table","furniture",[2.5,1,4])
TREADMILL=X("threadmill","furniture",[1,1.8,1])
BARBELL=X("barbell-stand","furniture",[1.5,1,0.5])
TREE=X("tree","outdoor",[1,5,1])
FIRTREE=X("fir-tree","outdoor",[0.5,3,0.5])
PALM=X("palm","outdoor",[0.5,3.7,0.5])
BUSH=X("bush","outdoor",[3,1.1,1])
UMBRELLA=X("patio-umbrella","outdoor",[1,1.2,1.5])
SUNBED=X("sunbed","outdoor",[1.5,1.5,0.5])
MEDFENCE=X("medium-fence","outdoor",[2,2,0.5])
LOFENCE=X("low-fence","outdoor",[2,0.8,0.5])
TESLA=X("tesla","outdoor",[2,1.7,5])
PARKING=X("parking-spot","outdoor",[5,1,2.5])
HOOP=X("basket-hoop","outdoor",[1,1.8,1])
PLAYHOUSE=X("outdoor-playhouse","outdoor",[0.5,0.5,1])
BALL=X("ball","outdoor",[0.5,0.3,0.5])
PILLAR=X("pillar","outdoor",[0.5,1.3,0.5])
STOOL=X("stool","furniture",[0.5,0.8,0.5])

H=3.5

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

# ============================================================================
# MODERN COMPOUND ESTATE — Multiple volumes, outdoor living
#
# Bird's eye view (each block is a separate building volume):
#
#  PARKING         MAIN HOUSE              MASTER WING
#  [-8,-2]         [0,0]=====[14,0]        [18,0]=====[26,0]
#   |  |           ‖  open-plan  ‖         ‖  master  ‖
#   |  |           ‖  living     ‖ covered ‖  suite   ‖
#   |  |           ‖  kitchen    ‖ breezwy ‖          ‖
#  [-8,8]          [0,8]=====[14,8]        [18,8]=====[26,8]
#
#                  COVERED TERRACE (open sides)
#                  [0,10]=====[14,14]
#                  (slab, columns, no full walls — outdoor dining)
#
#                        POOL AREA
#                  [2,16]~~~~~~~~~[12,22]
#                  (blue zone, sunbeds, umbrellas)
#
#                                          GUEST PAVILION
#                                          [20,14]====[28,14]
#                                          ‖ 2 beds   ‖
#                                          [20,20]====[28,20]
#
#  SPORTS AREA                    GARDEN + PLAYGROUND
#  [-6,16]----[-1,22]             [14,22]----[28,26]
#  (basketball, open)             (playhouse, trees)
#
# ============================================================================

async def main():
    b=B();await b.connect();print("[Compound Estate] Connected\n")
    await b.cmd("clear")
    bid=lid0=None
    for _ in range(10):
        await asyncio.sleep(1)
        st=await b.cmd("read_state");nodes=st.get("nodes",{})
        for nid,n in nodes.items():
            if n.get("type")=="building":bid=nid
            if n.get("type")=="level":lid0=nid
        if bid and lid0:break
    if not bid or not lid0:print("ERROR");await b.close();return

    L=lid0 # shorthand

    # ============================================================
    # VOLUME 1: MAIN HOUSE (0,0)-(14,8) — open plan, 14x8m
    # ============================================================
    print("=== MAIN HOUSE ===")
    await b.cmd("set_selection",selection={"levelId":L})

    # Slab
    await b.cmd("create_node",node={"type":"slab","polygon":[[0,0],[14,0],[14,8],[0,8]],"elevation":0.05},parentId=L)

    w=[]
    # Only 3 walls — south side is OPEN (floor-to-ceiling glass / terrace access)
    w.append(await W(b,L,[0,0],[14,0],0.25,H,True))    # 0: north
    w.append(await W(b,L,[14,0],[14,8],0.25,H,True))    # 1: east
    w.append(await W(b,L,[0,8],[0,0],0.25,H,True))      # 3: west
    # South wall has massive openings — make it a wall with big glass doors
    w.append(await W(b,L,[0,8],[14,8],0.25,H,True))      # 2: south

    # Interior: only a powder room partition, rest is open plan
    w.append(await W(b,L,[0,5],[3,5],0.12,H))            # 4: powder room north
    w.append(await W(b,L,[3,5],[3,8],0.12,H))            # 5: powder room east

    # Giant sliding doors on south wall
    await D(b,w[3],3,3.0,2.8)    # massive glass door center-left
    await D(b,w[3],10,3.0,2.8)   # massive glass door center-right

    # Windows
    await WN(b,w[0],3,3.0,2.4,0.3)      # north — panoramic
    await WN(b,w[0],10,3.0,2.4,0.3)     # north — panoramic
    await WN(b,w[1],4,2.5,2.4,0.3)      # east — floor to ceiling
    await WN(b,w[2],4,2.5,2.4,0.3)      # west — floor to ceiling

    # Zones — mostly open plan, just powder room is separate
    await b.cmd("create_node",node={"type":"zone","name":"Open Living","polygon":[[3,0],[14,0],[14,8],[3,8]],"color":"#3b82f6"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Entry","polygon":[[0,0],[3,0],[3,5],[0,5]],"color":"#d4a574"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Powder Room","polygon":[[0,5],[3,5],[3,8],[0,8]],"color":"#06b6d4"},parentId=L)

    await b.cmd("create_node",node={"type":"ceiling","polygon":[[0,0],[14,0],[14,8],[0,8]],"height":H},parentId=L)

    # Powder room door
    await D(b,w[4],1.5,0.7)

    # Furniture — open plan living/kitchen
    print("  Furnishing main house...")
    # Living area (right side, 4-14 x 0-4)
    await p(b,L,SOFA,[8,0,3],math.pi)
    await p(b,L,LIVCHAIR,[5,0,2],math.pi/4)
    await p(b,L,LOUNGE,[11,0,2],-math.pi/4)
    await p(b,L,COFFEE,[8,0,1.5])
    await p(b,L,TVSTAND,[8,0,0.5])
    await p(b,L,RNDCARPET,[8,0,2])
    await p(b,L,FLAMP,[4.5,0,0.5])
    await p(b,L,FLAMP,[12,0,0.5])

    # Kitchen island (right side, 9-13 x 5-7)
    await p(b,L,KCOUNTER,[11,0,5.5])
    await p(b,L,KCOUNTER,[13,0,7],math.pi/2)
    await p(b,L,FRIDGE,[13.3,0,5.5],math.pi)
    await p(b,L,STOVE,[11,0,7.3],math.pi)
    await p(b,L,STOOL,[10,0,5])
    await p(b,L,STOOL,[9,0,5])

    # Dining area (center, 5-9 x 5-7)
    await p(b,L,DTABLE,[6.5,0,6.5])
    await p(b,L,DCHAIR,[6.5,0,5.7],math.pi)
    await p(b,L,DCHAIR,[6.5,0,7.3])
    await p(b,L,DCHAIR,[5.3,0,6.5],math.pi/2)
    await p(b,L,DCHAIR,[7.7,0,6.5],-math.pi/2)

    await p(b,L,PLANT,[4,0,7.3])
    await p(b,L,PLANT,[13,0,3.5])

    # Powder room
    await p(b,L,TOILET,[1.5,0,7],math.pi)
    await p(b,L,SINK,[1.5,0,5.5])

    # ============================================================
    # COVERED BREEZEWAY (14,2)-(18,6) — connects main to master
    # Open sides, just a roof slab + columns
    # ============================================================
    print("\n=== COVERED BREEZEWAY ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[14,2],[18,2],[18,6],[14,6]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[14,2],[18,2],[18,6],[14,6]],"height":H},parentId=L)
    # Columns at corners (scaled up)
    await p(b,L,PILLAR,[14.3,0,2.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[17.7,0,2.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[14.3,0,5.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[17.7,0,5.7],0,[1,2.5,1])
    await b.cmd("create_node",node={"type":"zone","name":"Breezeway","polygon":[[14,2],[18,2],[18,6],[14,6]],"color":"#9ca3af"},parentId=L)
    await p(b,L,PLANT,[16,0,4])

    # ============================================================
    # VOLUME 2: MASTER WING (18,0)-(26,8) — private, 8x8m
    # ============================================================
    print("\n=== MASTER WING ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[18,0],[26,0],[26,8],[18,8]],"elevation":0.05},parentId=L)

    mw=[]
    for s,e in[([18,0],[26,0]),([26,0],[26,8]),([26,8],[18,8]),([18,8],[18,0])]:
        mw.append(await W(b,L,s,e,0.25,H,True))
    # Interior: bedroom / bathroom split
    mw.append(await W(b,L,[18,5],[26,5]))  # 4: horizontal
    mw.append(await W(b,L,[22,5],[22,8]))  # 5: bath/dressing

    await WN(b,mw[0],4,3.0,2.4,0.3)     # north panoramic
    await WN(b,mw[1],2.5,2.5,2.4,0.3)   # east
    await WN(b,mw[1],6,1.5,1.2,1.4)     # east bath
    await D(b,mw[2],4,1.2,2.4)           # south entrance from breezeway

    await D(b,mw[4],4)                    # bedroom->bath
    await D(b,mw[5],1.5,0.8)             # bath->dressing

    await b.cmd("create_node",node={"type":"zone","name":"Master Bedroom","polygon":[[18,0],[26,0],[26,5],[18,5]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Master Bath","polygon":[[18,5],[22,5],[22,8],[18,8]],"color":"#06b6d4"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Dressing","polygon":[[22,5],[26,5],[26,8],[22,8]],"color":"#a78bfa"},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[18,0],[26,0],[26,8],[18,8]],"height":H},parentId=L)

    print("  Furnishing master wing...")
    await p(b,L,DBED,[22,0,1.5])
    await p(b,L,BSIDE,[20,0,1.5])
    await p(b,L,BSIDE,[24,0,1.5])
    await p(b,L,RNDCARPET,[22,0,3])
    await p(b,L,FLAMP,[19,0,0.5])
    await p(b,L,FLAMP,[25,0,0.5])
    await p(b,L,LOUNGE,[19,0,4],-math.pi/4)
    await p(b,L,SPLANT,[25,0,4])
    # Bath
    await p(b,L,BATHTUB,[20,0,6.5])
    await p(b,L,SINK,[19,0,7.5],math.pi)
    # Dressing
    await p(b,L,CLOSET,[23,0,5.5])
    await p(b,L,CLOSET,[25,0,5.5])
    await p(b,L,DRESSER,[24,0,7.5],math.pi)

    # ============================================================
    # COVERED TERRACE (0,10)-(14,14) — outdoor dining, open air
    # Only back wall + side walls halfway, rest is open
    # ============================================================
    print("\n=== COVERED TERRACE ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[0,10],[14,10],[14,14],[0,14]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[0,10],[14,10],[14,14],[0,14]],"height":H},parentId=L)
    # Short walls on sides only (half height for open feel)
    await W(b,L,[0,10],[0,14],0.2,1.0,True)
    await W(b,L,[14,10],[14,14],0.2,1.0,True)
    # Columns
    await p(b,L,PILLAR,[0.3,0,10.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[13.7,0,10.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[0.3,0,13.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[7,0,13.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[13.7,0,13.7],0,[1,2.5,1])

    await b.cmd("create_node",node={"type":"zone","name":"Covered Terrace","polygon":[[0,10],[14,10],[14,14],[0,14]],"color":"#92400e"},parentId=L)

    # Outdoor dining on terrace
    await p(b,L,DTABLE,[7,0,12])
    await p(b,L,DCHAIR,[7,0,11.2],math.pi)
    await p(b,L,DCHAIR,[7,0,12.8])
    await p(b,L,DCHAIR,[5.8,0,12],math.pi/2)
    await p(b,L,DCHAIR,[8.2,0,12],-math.pi/2)
    await p(b,L,DCHAIR,[5.8,0,11.2],math.pi/2)
    await p(b,L,DCHAIR,[8.2,0,11.2],-math.pi/2)
    await p(b,L,PLANT,[1,0,11])
    await p(b,L,PLANT,[13,0,11])
    await p(b,L,PLANT,[1,0,13])
    await p(b,L,PLANT,[13,0,13])

    # ============================================================
    # POOL AREA (2,16)-(12,22) — blue zone, sunbeds, umbrellas
    # ============================================================
    print("\n=== POOL AREA ===")
    # Pool "slab" at lower elevation (simulates water surface)
    await b.cmd("create_node",node={"type":"slab","polygon":[[3,16],[11,16],[11,21],[3,21]],"elevation":-0.5},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Swimming Pool","polygon":[[3,16],[11,16],[11,21],[3,21]],"color":"#0284c7"},parentId=L)

    # Pool deck (surrounding slab)
    await b.cmd("create_node",node={"type":"slab","polygon":[[1,15],[13,15],[13,23],[1,23]],"elevation":0.02,
        "holes":[[[3,16],[11,16],[11,21],[3,21]]]},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Pool Deck","polygon":[[1,15],[13,15],[13,23],[1,23]],"color":"#d4a574"},parentId=L)

    # Low fence around pool
    await W(b,L,[1,15],[13,15],0.05,0.8)
    await W(b,L,[13,15],[13,23],0.05,0.8)
    await W(b,L,[13,23],[1,23],0.05,0.8)
    await W(b,L,[1,23],[1,15],0.05,0.8)

    # Pool furniture
    await p(b,L,SUNBED,[2,0,17],math.pi/2)
    await p(b,L,SUNBED,[2,0,19],math.pi/2)
    await p(b,L,UMBRELLA,[2,0,18])
    await p(b,L,SUNBED,[12,0,17],-math.pi/2)
    await p(b,L,SUNBED,[12,0,19],-math.pi/2)
    await p(b,L,UMBRELLA,[12,0,18])
    await p(b,L,SUNBED,[7,0,22])
    await p(b,L,UMBRELLA,[5,0,22])

    # ============================================================
    # GUEST PAVILION (20,14)-(28,20) — separate building, 8x6m
    # ============================================================
    print("\n=== GUEST PAVILION ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[20,14],[28,14],[28,20],[20,20]],"elevation":0.05},parentId=L)

    gw=[]
    for s,e in[([20,14],[28,14]),([28,14],[28,20]),([28,20],[20,20]),([20,20],[20,14])]:
        gw.append(await W(b,L,s,e,0.2,H,True))
    gw.append(await W(b,L,[24,14],[24,20]))  # 4: room divider
    gw.append(await W(b,L,[20,17],[24,17]))  # 5: bed/bath in left room

    await D(b,gw[0],2,1.0,2.2)     # entrance 1
    await D(b,gw[0],6,1.0,2.2)     # entrance 2
    await D(b,gw[5],2,0.7)         # bath door
    await WN(b,gw[1],3,1.5,1.6)    # east window
    await WN(b,gw[2],6,1.5,1.6)    # south window
    await WN(b,gw[3],3,1.5,1.6)    # west window

    await b.cmd("create_node",node={"type":"zone","name":"Guest Room 1","polygon":[[20,14],[24,14],[24,17],[20,17]],"color":"#8b5cf6"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Guest Bath","polygon":[[20,17],[24,17],[24,20],[20,20]],"color":"#06b6d4"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Guest Room 2","polygon":[[24,14],[28,14],[28,20],[24,20]],"color":"#a855f7"},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[20,14],[28,14],[28,20],[20,20]],"height":H},parentId=L)

    print("  Furnishing guest pavilion...")
    await p(b,L,DBED,[22,0,15.5])
    await p(b,L,BSIDE,[20.5,0,15.5])
    await p(b,L,SPLANT,[23.5,0,14.5])
    await p(b,L,TOILET,[22,0,19],math.pi)
    await p(b,L,SINK,[22,0,17.5])
    await p(b,L,DBED,[26,0,17])
    await p(b,L,BSIDE,[27.5,0,17])
    await p(b,L,CLOSET,[25,0,19.3],math.pi)

    # ============================================================
    # PARKING AREA — driveway + carport
    # ============================================================
    print("\n=== PARKING ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[-8,-2],[-1,-2],[-1,8],[-8,8]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Parking","polygon":[[-8,-2],[-1,-2],[-1,8],[-8,8]],"color":"#44403c"},parentId=L)
    # Carport roof (no walls)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-8,-2],[-1,-2],[-1,5],[-8,5]],"height":3.0},parentId=L)
    await p(b,L,PILLAR,[-7.5,0,-1.5],0,[1,2,1])
    await p(b,L,PILLAR,[-1.5,0,-1.5],0,[1,2,1])
    await p(b,L,PILLAR,[-7.5,0,4.5],0,[1,2,1])
    await p(b,L,PILLAR,[-1.5,0,4.5],0,[1,2,1])
    await p(b,L,TESLA,[-4.5,0,0])
    await p(b,L,TESLA,[-4.5,0,3])

    # ============================================================
    # SPORTS AREA — basketball court
    # ============================================================
    print("\n=== SPORTS & PLAY AREAS ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[-6,16],[-1,16],[-1,22],[-6,22]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Sports Court","polygon":[[-6,16],[-1,16],[-1,22],[-6,22]],"color":"#ea580c"},parentId=L)
    await p(b,L,HOOP,[-3.5,0,16.5])
    await p(b,L,HOOP,[-3.5,0,21.5],math.pi)
    await p(b,L,BALL,[-3,0,19])

    # Playground area
    await p(b,L,PLAYHOUSE,[16,0,24])
    await p(b,L,BALL,[17,0,24])

    # ============================================================
    # OUTDOOR LANDSCAPE — deliberate, not filling every gap
    # ============================================================
    print("\n=== LANDSCAPE ===")

    # Garden path (narrow slab connecting areas)
    await b.cmd("create_node",node={"type":"slab","polygon":[[14,12],[20,12],[20,14],[14,14]],"elevation":0.02},parentId=L)

    # Trees — strategically placed, not a wall
    for pos in[[-3,0,-4],[15,0,-3],[29,0,-2],[30,0,5],[30,0,12],[-4,0,12],[-4,0,20],[15,0,26],[25,0,24],[30,0,18]]:
        await p(b,L,TREE,pos)

    # Palms — tropical accent
    for pos in[[16,0,9],[27,0,10],[0,0,15],[-7,0,14],[14,0,22],[0,0,24]]:
        await p(b,L,PALM,pos)

    # Fir trees — privacy screening
    for pos in[[-6,0,-3],[-6,0,0],[-6,0,3],[-6,0,6],[-6,0,9],[30,0,-1],[30,0,2]]:
        await p(b,L,FIRTREE,pos)

    # Bushes — garden beds
    for pos in[[2,0,-2],[6,0,-2],[10,0,-2],[22,0,-2],[26,0,-2],[17,0,22],[22,0,22],[15,0,10],[27,0,12]]:
        await p(b,L,BUSH,pos)

    # Scattered plants and accents
    await p(b,L,SPLANT,[16,0,14])
    await p(b,L,SPLANT,[19,0,12])
    await p(b,L,PLANT,[28,0,9])

    # Garden seating (between pool and guest house)
    await p(b,L,UMBRELLA,[16,0,18])
    await p(b,L,SUNBED,[15,0,19])
    await p(b,L,SUNBED,[17,0,19])

    print("  Landscape DONE!")

    print(f"\n{'='*60}")
    print("  MODERN COMPOUND ESTATE COMPLETE")
    print("  ────────────────────────────────────────")
    print("  MAIN HOUSE (14x8m):")
    print("    Open-plan living/kitchen/dining")
    print("    Floor-to-ceiling windows, south opens to terrace")
    print("")
    print("  COVERED BREEZEWAY:")
    print("    Columns, plants — connects to master wing")
    print("")
    print("  MASTER WING (8x8m, separate volume):")
    print("    Bedroom, spa bath, walk-in dressing")
    print("")
    print("  COVERED TERRACE (14x4m, open air):")
    print("    Outdoor dining for 6, columns, plants")
    print("")
    print("  SWIMMING POOL (8x5m):")
    print("    Pool deck, 5 sunbeds, 3 parasols")
    print("")
    print("  GUEST PAVILION (8x6m, separate building):")
    print("    2 guest rooms + shared bath")
    print("")
    print("  PARKING (carport):")
    print("    2 Teslas, covered parking with columns")
    print("")
    print("  SPORTS COURT:")
    print("    Basketball hoops, playground area")
    print("")
    print("  LANDSCAPE:")
    print("    Trees, palms, firs, bushes, garden seating")
    print("  ────────────────────────────────────────")
    print("  Deliberate negative space throughout")
    print("  3.5m ceilings, open-air structures")
    print(f"{'='*60}")
    await b.close()

if __name__=="__main__":
    asyncio.run(main())
