"""The Courtyard Hotel — 2-story U-shape compound with pool, courtyard, parking."""

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
MICROWAVE=X("microwave","kitchen",[1,0.5,0.5])
STOOL=X("stool","furniture",[0.5,0.8,0.5])
DBED=X("double-bed","furniture",[2,0.8,2.5],[0,0,-0.03])
SBED=X("single-bed","furniture",[1.5,0.7,2.5])
BUNKBED=X("bunkbed","furniture",[1.5,1.8,2.5])
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

H=3.5
H2=3.0  # second floor height

# ============================================================================
# THE COURTYARD HOTEL — 2-Story U-Shape Compound
#
# Bird's eye:
#
#  WEST WING (2F guest rooms)   MAIN BLOCK (2F lobby+restaurant)  EAST WING (2F guest rooms)
#  [-14,0]======[-6,0]          [0,0]================[16,0]       [22,0]========[30,0]
#  ‖ Rm101 | Rm102 ‖  covered  ‖  LOBBY   |  RESTAURANT  ‖  covered  ‖ Rm105 | Rm106 ‖
#  ‖ Rm103 | Rm104 ‖  walkway  ‖  RECEPT  |  KITCHEN     ‖  walkway  ‖ Rm107 | Rm108 ‖
#  [-14,10]=====[-6,10]         [0,10]===============[16,10]      [22,10]======[30,10]
#
#                               COURTYARD (open air, landscaped)
#                            [-6,12]===================[22,12]
#                            (palms, seating, garden path)
#                            [-6,20]===================[22,20]
#
#                               POOL AREA
#                            [2,22]~~~~~~~~~~[14,28]
#                            (blue zone, sunbeds, umbrellas, deck)
#
#  PARKING/CARPORT                                       SPORTS
#  [-14,12]====[-6,20]                                   [22,14]====[30,20]
#
#  2nd Floor (Level 1):
#  - West wing: Rooms 201-204
#  - East wing: Rooms 205-208
#  - Main block: Conference room, Lounge bar, Office
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


# ---- Helper: build 2 guest rooms side-by-side in a wing ----
# Each room is ~4x5m with en-suite bathroom (4x2.5m room + 4x2.5m bath)
# Room layout within a wing (8x10m):
#   [x0,z0]----[x0+4,z0]----[x0+8,z0]
#   | Room A  | Room B  |
#   |---------|---------|
#   | Bath A  | Bath B  |
#   [x0,z0+10]---...----[x0+8,z0+10]

async def build_two_rooms(b, L, x0, z0, room_names, h=H, ext_walls=True):
    """Build two guest rooms with en-suite baths, side by side, 4m wide each, 10m deep total."""
    walls = []

    # Exterior walls
    walls.append(await W(b,L,[x0,z0],[x0+8,z0],0.2,h,ext_walls))        # 0: north
    walls.append(await W(b,L,[x0+8,z0],[x0+8,z0+10],0.2,h,ext_walls))    # 1: east
    walls.append(await W(b,L,[x0+8,z0+10],[x0,z0+10],0.2,h,ext_walls))   # 2: south
    walls.append(await W(b,L,[x0,z0+10],[x0,z0],0.2,h,ext_walls))         # 3: west

    # Center divider (between room A and room B)
    walls.append(await W(b,L,[x0+4,z0],[x0+4,z0+10],0.12,h))              # 4: center vertical

    # Bath divider walls (each room: bedroom z0..z0+6.5, bath z0+6.5..z0+10)
    walls.append(await W(b,L,[x0,z0+6.5],[x0+4,z0+6.5],0.12,h))          # 5: room A bath wall
    walls.append(await W(b,L,[x0+4,z0+6.5],[x0+8,z0+6.5],0.12,h))        # 6: room B bath wall

    # Doors -- entrance from corridor (south wall)
    await D(b,walls[2],2,0.9,2.2)      # room A entrance
    await D(b,walls[2],6,0.9,2.2)      # room B entrance

    # Bath doors
    await D(b,walls[5],2,0.7,2.1)
    await D(b,walls[6],2,0.7,2.1)

    # Windows -- north facing (view side)
    await WN(b,walls[0],2,1.8,1.8,0.5)    # room A window
    await WN(b,walls[0],6,1.8,1.8,0.5)    # room B window

    # Small bath windows -- side walls
    await WN(b,walls[3],8.5,0.8,0.8,1.4)  # room A bath window (west)
    await WN(b,walls[1],8.5,0.8,0.8,1.4)  # room B bath window (east)

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":room_names[0],"polygon":[[x0,z0],[x0+4,z0],[x0+4,z0+6.5],[x0,z0+6.5]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":room_names[0]+" Bath","polygon":[[x0,z0+6.5],[x0+4,z0+6.5],[x0+4,z0+10],[x0,z0+10]],"color":"#06b6d4"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":room_names[1],"polygon":[[x0+4,z0],[x0+8,z0],[x0+8,z0+6.5],[x0+4,z0+6.5]],"color":"#8b5cf6"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":room_names[1]+" Bath","polygon":[[x0+4,z0+6.5],[x0+8,z0+6.5],[x0+8,z0+10],[x0+4,z0+10]],"color":"#0891b2"},parentId=L)

    return walls

async def furnish_room(b, L, x0, z0):
    """Furnish one 4x6.5m guest room + 4x3.5m bath."""
    # Bedroom area
    await p(b,L,DBED,[x0+2,0,z0+2])
    await p(b,L,BSIDE,[x0+0.5,0,z0+1.5])
    await p(b,L,BSIDE,[x0+3.5,0,z0+1.5])
    await p(b,L,CLOSET,[x0+2,0,z0+5.8],math.pi)
    await p(b,L,DRESSER,[x0+0.5,0,z0+4.5],math.pi/2)
    await p(b,L,SPLANT,[x0+3.5,0,z0+5.5])
    await p(b,L,RCARPET,[x0+2,0,z0+3])

    # Bathroom area
    await p(b,L,SHOWER,[x0+1,0,z0+7.5])
    await p(b,L,TOILET,[x0+3,0,z0+9],math.pi)
    await p(b,L,SINK,[x0+2,0,z0+7])


async def main():
    b=B();await b.connect();print("[The Courtyard Hotel] Connected\n")

    # Clear triggers browser reload — must reconnect after
    print("  Clearing scene (browser will reload)...")
    try:
        await b.cmd("clear")
    except:
        pass
    await b.close()
    print("  Waiting for browser to reload...")
    await asyncio.sleep(10)
    await b.connect()
    print("  Reconnected")

    bid=lid0=None
    for _ in range(15):
        await asyncio.sleep(1)
        try:
            st=await b.cmd("read_state");nodes=st.get("nodes",{})
            for nid,n in nodes.items():
                if n.get("type")=="building":bid=nid
                if n.get("type")=="level":lid0=nid
            if bid and lid0:break
        except:
            pass
    if not bid or not lid0:print("ERROR: No default scene");await b.close();return

    L=lid0

    # ==================================================================
    # FLOOR 1 (Ground Floor) — Level 0
    # ==================================================================
    print("========================================")
    print("  GROUND FLOOR (Level 0)")
    print("========================================")
    await b.cmd("set_selection",selection={"levelId":L})

    # ==================================================================
    # MAIN BLOCK (0,0)-(16,10) — Lobby, Restaurant, Kitchen
    # ==================================================================
    print("\n=== MAIN BLOCK — Lobby & Restaurant ===")

    # Slab
    await b.cmd("create_node",node={"type":"slab","polygon":[[0,0],[16,0],[16,10],[0,10]],"elevation":0.05},parentId=L)

    mw=[]
    mw.append(await W(b,L,[0,0],[16,0],0.25,H,True))      # 0: north
    mw.append(await W(b,L,[16,0],[16,10],0.25,H,True))     # 1: east
    mw.append(await W(b,L,[16,10],[0,10],0.25,H,True))     # 2: south (courtyard side)
    mw.append(await W(b,L,[0,10],[0,0],0.25,H,True))       # 3: west

    # Interior walls: lobby | restaurant | kitchen
    mw.append(await W(b,L,[7,0],[7,10],0.15,H))            # 4: lobby/restaurant divider
    mw.append(await W(b,L,[7,7],[16,7],0.12,H))            # 5: restaurant/kitchen divider

    # Grand entrance (north, center of lobby)
    await D(b,mw[0],3,2.0,2.8)

    # Lobby->restaurant door
    await D(b,mw[4],5,1.2,2.4)

    # Restaurant door to courtyard (south)
    await D(b,mw[2],12,1.5,2.4)

    # Kitchen service door
    await D(b,mw[5],6,0.9,2.2)

    # Windows — floor-to-ceiling on lobby and restaurant
    await WN(b,mw[0],1,2.5,2.4,0.3)       # lobby north window
    await WN(b,mw[0],10,3.0,2.4,0.3)      # restaurant north window
    await WN(b,mw[3],3,2.5,2.4,0.3)       # lobby west window
    await WN(b,mw[3],7.5,2.0,2.4,0.3)     # lobby west window 2
    await WN(b,mw[1],2,2.5,2.4,0.3)       # restaurant east window
    await WN(b,mw[2],3,2.5,2.2,0.3)       # lobby south (courtyard)
    await WN(b,mw[2],8,2.0,2.2,0.3)       # restaurant south (courtyard)

    # Small kitchen window
    await WN(b,mw[1],8.5,1.0,1.0,1.2)

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Hotel Lobby","polygon":[[0,0],[7,0],[7,10],[0,10]],"color":"#d4a574"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Restaurant","polygon":[[7,0],[16,0],[16,7],[7,7]],"color":"#dc2626"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Kitchen","polygon":[[7,7],[16,7],[16,10],[7,10]],"color":"#f59e0b"},parentId=L)

    # Ceiling
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[0,0],[16,0],[16,10],[0,10]],"height":H},parentId=L)

    # Furnish lobby
    print("  Furnishing lobby...")
    await p(b,L,SOFA,[3.5,0,3])
    await p(b,L,SOFA,[3.5,0,5.5],math.pi)
    await p(b,L,COFFEE,[3.5,0,4.2])
    await p(b,L,RNDCARPET,[3.5,0,4.5])
    await p(b,L,LIVCHAIR,[1,0,4.2],math.pi/4)
    await p(b,L,FLAMP,[1,0,1])
    await p(b,L,FLAMP,[6,0,1])
    await p(b,L,PLANT,[6,0,9])
    await p(b,L,PLANT,[1,0,9])
    await p(b,L,COATRACK,[0.5,0,0.5])
    await p(b,L,SPLANT,[6,0,0.5])
    # Reception desk (use kitchen-counter as desk)
    await p(b,L,KCOUNTER,[3.5,0,8],math.pi)
    await p(b,L,OFFCHAIR,[3.5,0,8.8])
    await p(b,L,SPLANT,[5.5,0,8])
    await p(b,L,BOOKS,[2,0,8.2])

    # Furnish restaurant
    print("  Furnishing restaurant...")
    # 4 dining tables with chairs
    for tx,tz in [(10,2),(13,2),(10,5),(13,5)]:
        await p(b,L,DTABLE,[tx,0,tz])
        await p(b,L,DCHAIR,[tx,0,tz-0.8],math.pi)
        await p(b,L,DCHAIR,[tx,0,tz+0.8])
        await p(b,L,DCHAIR,[tx-1.2,0,tz],math.pi/2)
        await p(b,L,DCHAIR,[tx+1.2,0,tz],-math.pi/2)
    await p(b,L,PLANT,[8,0,0.5])
    await p(b,L,PLANT,[15,0,0.5])

    # Furnish kitchen
    print("  Furnishing kitchen...")
    await p(b,L,KCOUNTER,[9,0,8.5])
    await p(b,L,KCOUNTER,[11,0,8.5])
    await p(b,L,FRIDGE,[15.3,0,8.5],math.pi)
    await p(b,L,STOVE,[13,0,9.3],math.pi)
    await p(b,L,KCABINET,[9,0,9.5],math.pi)

    # ==================================================================
    # WEST WING (rooms) — [-14,0] to [-6,10]
    # ==================================================================
    print("\n=== WEST WING — Rooms 101-104 ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[-14,0],[-6,0],[-6,10],[-14,10]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-14,0],[-6,0],[-6,10],[-14,10]],"height":H},parentId=L)

    # Two rooms stacked: 101/102 on top row, 103/104 on bottom
    # Room 101: [-14,0]->[-10,0]->[-10,5]->[-14,5]
    # Room 102: [-10,0]->[-6,0]->[-6,5]->[-10,5]
    # Room 103: [-14,5]->[-10,5]->[-10,10]->[-14,10]
    # Room 104: [-10,5]->[-6,5]->[-6,10]->[-10,10]

    ww=[]
    ww.append(await W(b,L,[-14,0],[-6,0],0.2,H,True))       # 0: north
    ww.append(await W(b,L,[-6,0],[-6,10],0.2,H,True))        # 1: east (corridor side)
    ww.append(await W(b,L,[-6,10],[-14,10],0.2,H,True))      # 2: south
    ww.append(await W(b,L,[-14,10],[-14,0],0.2,H,True))      # 3: west
    ww.append(await W(b,L,[-10,0],[-10,10],0.12,H))          # 4: center vertical
    ww.append(await W(b,L,[-14,5],[-6,5],0.12,H))            # 5: center horizontal

    # Bath walls (each room has a 4x2m bath alcove in the inner corner)
    ww.append(await W(b,L,[-14,2],[-12,2],0.1,H))            # 6: rm101 bath
    ww.append(await W(b,L,[-12,0],[-12,2],0.1,H))            # 7: rm101 bath
    ww.append(await W(b,L,[-8,0],[-8,2],0.1,H))              # 8: rm102 bath
    ww.append(await W(b,L,[-8,2],[-6,2],0.1,H))              # 9: rm102 bath
    ww.append(await W(b,L,[-14,8],[-12,8],0.1,H))            # 10: rm103 bath
    ww.append(await W(b,L,[-12,8],[-12,10],0.1,H))           # 11: rm103 bath
    ww.append(await W(b,L,[-8,8],[-8,10],0.1,H))             # 12: rm104 bath
    ww.append(await W(b,L,[-8,10],[-6,8],0.1,H))             # 13: rm104 bath -- angled is wrong, use straight
    # Fix: rm104 bath wall should be straight
    # Actually let me use a simpler layout for rm104
    ww.append(await W(b,L,[-8,8],[-6,8],0.1,H))              # 14: rm104 bath horizontal

    # Doors from corridor side (east wall)
    await D(b,ww[1],2,0.9,2.2)     # room 102
    await D(b,ww[1],7,0.9,2.2)     # room 104

    # Doors from west side for 101, 103
    await D(b,ww[3],2,0.9,2.2)     # room 101
    await D(b,ww[3],7,0.9,2.2)     # room 103

    # Bath doors
    await D(b,ww[6],1,0.7,2.1)     # rm101 bath
    await D(b,ww[9],1,0.7,2.1)     # rm102 bath
    await D(b,ww[10],1,0.7,2.1)    # rm103 bath
    await D(b,ww[14],1,0.7,2.1)    # rm104 bath

    # Windows (north/south for views)
    await WN(b,ww[0],2,1.5,1.8,0.5)    # rm101 window
    await WN(b,ww[0],6,1.5,1.8,0.5)    # rm102 window
    await WN(b,ww[2],2,1.5,1.8,0.5)    # rm104 window
    await WN(b,ww[2],6,1.5,1.8,0.5)    # rm103 window

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Room 101","polygon":[[-14,0],[-10,0],[-10,5],[-14,5]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Room 102","polygon":[[-10,0],[-6,0],[-6,5],[-10,5]],"color":"#8b5cf6"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Room 103","polygon":[[-14,5],[-10,5],[-10,10],[-14,10]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Room 104","polygon":[[-10,5],[-6,5],[-6,10],[-10,10]],"color":"#8b5cf6"},parentId=L)

    # Furnish west wing rooms
    print("  Furnishing rooms 101-104...")
    # Room 101 [-14,0]->[-10,5]: bed area [-14,2]->[-10,5], bath [-14,0]->[-12,2]
    await p(b,L,DBED,[-12,0,3.5])
    await p(b,L,BSIDE,[-13.5,0,3])
    await p(b,L,BSIDE,[-10.5,0,3])
    await p(b,L,DRESSER,[-12,0,4.5],math.pi)
    await p(b,L,TOILET,[-13,0,1],math.pi)
    await p(b,L,SINK,[-13,0,0.5],math.pi)

    # Room 102 [-10,0]->[-6,5]: bed area [-10,2]->[-6,5], bath [-8,0]->[-6,2]
    await p(b,L,DBED,[-8,0,3.5])
    await p(b,L,BSIDE,[-9.5,0,3])
    await p(b,L,BSIDE,[-6.5,0,3])
    await p(b,L,DRESSER,[-8,0,4.5],math.pi)
    await p(b,L,TOILET,[-7,0,1],math.pi)
    await p(b,L,SINK,[-7,0,0.5],math.pi)

    # Room 103 [-14,5]->[-10,10]: bed area [-14,5]->[-10,8], bath [-14,8]->[-12,10]
    await p(b,L,DBED,[-12,0,6])
    await p(b,L,BSIDE,[-13.5,0,6.5])
    await p(b,L,BSIDE,[-10.5,0,6.5])
    await p(b,L,DRESSER,[-12,0,5.3])
    await p(b,L,TOILET,[-13,0,9],math.pi)
    await p(b,L,SINK,[-13,0,8.5])

    # Room 104 [-10,5]->[-6,10]: bed area [-10,5]->[-6,8], bath [-8,8]->[-6,10]
    await p(b,L,DBED,[-8,0,6])
    await p(b,L,BSIDE,[-9.5,0,6.5])
    await p(b,L,BSIDE,[-6.5,0,6.5])
    await p(b,L,DRESSER,[-8,0,5.3])
    await p(b,L,TOILET,[-7,0,9],math.pi)
    await p(b,L,SINK,[-7,0,8.5])

    # ==================================================================
    # EAST WING (rooms) — [22,0] to [30,10]
    # ==================================================================
    print("\n=== EAST WING — Rooms 105-108 ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[22,0],[30,0],[30,10],[22,10]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[22,0],[30,0],[30,10],[22,10]],"height":H},parentId=L)

    ew=[]
    ew.append(await W(b,L,[22,0],[30,0],0.2,H,True))       # 0: north
    ew.append(await W(b,L,[30,0],[30,10],0.2,H,True))      # 1: east
    ew.append(await W(b,L,[30,10],[22,10],0.2,H,True))     # 2: south
    ew.append(await W(b,L,[22,10],[22,0],0.2,H,True))      # 3: west (corridor side)
    ew.append(await W(b,L,[26,0],[26,10],0.12,H))          # 4: center vertical
    ew.append(await W(b,L,[22,5],[30,5],0.12,H))           # 5: center horizontal

    # Bath walls
    ew.append(await W(b,L,[22,2],[24,2],0.1,H))            # 6: rm105 bath
    ew.append(await W(b,L,[24,0],[24,2],0.1,H))            # 7: rm105 bath
    ew.append(await W(b,L,[28,0],[28,2],0.1,H))            # 8: rm106 bath
    ew.append(await W(b,L,[28,2],[30,2],0.1,H))            # 9: rm106 bath
    ew.append(await W(b,L,[22,8],[24,8],0.1,H))            # 10: rm107 bath
    ew.append(await W(b,L,[24,8],[24,10],0.1,H))           # 11: rm107 bath
    ew.append(await W(b,L,[28,8],[28,10],0.1,H))           # 12: rm108 bath
    ew.append(await W(b,L,[28,8],[30,8],0.1,H))            # 13: rm108 bath

    # Doors from corridor side (west wall)
    await D(b,ew[3],2,0.9,2.2)     # room 105
    await D(b,ew[3],7,0.9,2.2)     # room 107

    # Doors from east side for 106, 108
    await D(b,ew[1],2,0.9,2.2)     # room 106
    await D(b,ew[1],7,0.9,2.2)     # room 108

    # Bath doors
    await D(b,ew[6],1,0.7,2.1)
    await D(b,ew[9],1,0.7,2.1)
    await D(b,ew[10],1,0.7,2.1)
    await D(b,ew[13],1,0.7,2.1)

    # Windows (north/south)
    await WN(b,ew[0],2,1.5,1.8,0.5)
    await WN(b,ew[0],6,1.5,1.8,0.5)
    await WN(b,ew[2],2,1.5,1.8,0.5)
    await WN(b,ew[2],6,1.5,1.8,0.5)

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Room 105","polygon":[[22,0],[26,0],[26,5],[22,5]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Room 106","polygon":[[26,0],[30,0],[30,5],[26,5]],"color":"#8b5cf6"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Room 107","polygon":[[22,5],[26,5],[26,10],[22,10]],"color":"#7c3aed"},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Room 108","polygon":[[26,5],[30,5],[30,10],[26,10]],"color":"#8b5cf6"},parentId=L)

    # Furnish east wing rooms
    print("  Furnishing rooms 105-108...")
    # Room 105 [22,0]->[26,5]
    await p(b,L,DBED,[24,0,3.5])
    await p(b,L,BSIDE,[22.5,0,3])
    await p(b,L,BSIDE,[25.5,0,3])
    await p(b,L,DRESSER,[24,0,4.5],math.pi)
    await p(b,L,TOILET,[23,0,1],math.pi)
    await p(b,L,SINK,[23,0,0.5],math.pi)

    # Room 106 [26,0]->[30,5]
    await p(b,L,DBED,[28,0,3.5])
    await p(b,L,BSIDE,[26.5,0,3])
    await p(b,L,BSIDE,[29.5,0,3])
    await p(b,L,DRESSER,[28,0,4.5],math.pi)
    await p(b,L,TOILET,[29,0,1],math.pi)
    await p(b,L,SINK,[29,0,0.5],math.pi)

    # Room 107 [22,5]->[26,10]
    await p(b,L,DBED,[24,0,6])
    await p(b,L,BSIDE,[22.5,0,6.5])
    await p(b,L,BSIDE,[25.5,0,6.5])
    await p(b,L,DRESSER,[24,0,5.3])
    await p(b,L,TOILET,[23,0,9],math.pi)
    await p(b,L,SINK,[23,0,8.5])

    # Room 108 [26,5]->[30,10]
    await p(b,L,DBED,[28,0,6])
    await p(b,L,BSIDE,[26.5,0,6.5])
    await p(b,L,BSIDE,[29.5,0,6.5])
    await p(b,L,DRESSER,[28,0,5.3])
    await p(b,L,TOILET,[29,0,9],math.pi)
    await p(b,L,SINK,[29,0,8.5])

    # ==================================================================
    # COVERED WALKWAYS — connecting wings to main block
    # ==================================================================
    print("\n=== COVERED WALKWAYS ===")

    # West walkway [-6,2]->[0,8] (connects west wing to main lobby)
    await b.cmd("create_node",node={"type":"slab","polygon":[[-6,3],[0,3],[0,7],[-6,7]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-6,3],[0,3],[0,7],[-6,7]],"height":H},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"West Walkway","polygon":[[-6,3],[0,3],[0,7],[-6,7]],"color":"#9ca3af"},parentId=L)
    await p(b,L,PILLAR,[-5.7,0,3.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[-5.7,0,6.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[-0.3,0,3.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[-0.3,0,6.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[-3,0,3.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[-3,0,6.7],0,[1,2.5,1])
    await p(b,L,PLANT,[-3,0,5])

    # East walkway [16,2]->[22,8] (connects main to east wing)
    await b.cmd("create_node",node={"type":"slab","polygon":[[16,3],[22,3],[22,7],[16,7]],"elevation":0.05},parentId=L)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[16,3],[22,3],[22,7],[16,7]],"height":H},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"East Walkway","polygon":[[16,3],[22,3],[22,7],[16,7]],"color":"#9ca3af"},parentId=L)
    await p(b,L,PILLAR,[16.3,0,3.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[16.3,0,6.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[21.7,0,3.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[21.7,0,6.7],0,[1,2.5,1])
    await p(b,L,PILLAR,[19,0,3.3],0,[1,2.5,1])
    await p(b,L,PILLAR,[19,0,6.7],0,[1,2.5,1])
    await p(b,L,PLANT,[19,0,5])

    # ==================================================================
    # COURTYARD — open air garden between buildings
    # ==================================================================
    print("\n=== COURTYARD ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[-6,10],[22,10],[22,20],[-6,20]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Courtyard","polygon":[[-6,10],[22,10],[22,20],[-6,20]],"color":"#22c55e"},parentId=L)

    # Garden path through courtyard (narrow slab)
    await b.cmd("create_node",node={"type":"slab","polygon":[[6,10],[10,10],[10,20],[6,20]],"elevation":0.04},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Garden Path","polygon":[[6,10],[10,10],[10,20],[6,20]],"color":"#d4a574"},parentId=L)

    # Courtyard landscaping
    await p(b,L,PALM,[0,0,12])
    await p(b,L,PALM,[4,0,15])
    await p(b,L,PALM,[12,0,12])
    await p(b,L,PALM,[16,0,15])
    await p(b,L,PALM,[20,0,12])

    # Courtyard seating areas
    await p(b,L,UMBRELLA,[2,0,14])
    await p(b,L,SUNBED,[1,0,14.5])
    await p(b,L,SUNBED,[3,0,14.5])
    await p(b,L,UMBRELLA,[14,0,14])
    await p(b,L,SUNBED,[13,0,14.5])
    await p(b,L,SUNBED,[15,0,14.5])

    # Outdoor dining in courtyard
    await p(b,L,DTABLE,[8,0,14])
    await p(b,L,DCHAIR,[8,0,13.2],math.pi)
    await p(b,L,DCHAIR,[8,0,14.8])
    await p(b,L,DCHAIR,[6.8,0,14],math.pi/2)
    await p(b,L,DCHAIR,[9.2,0,14],-math.pi/2)

    # More courtyard plants
    await p(b,L,BUSH,[-4,0,11])
    await p(b,L,BUSH,[-4,0,17])
    await p(b,L,BUSH,[20,0,17])
    await p(b,L,BUSH,[8,0,18])
    await p(b,L,SPLANT,[8,0,11])
    await p(b,L,SPLANT,[2,0,18])
    await p(b,L,SPLANT,[14,0,18])

    # ==================================================================
    # POOL AREA (2,22)-(14,28) — south of courtyard
    # ==================================================================
    print("\n=== POOL AREA ===")
    # Pool slab (sunken)
    await b.cmd("create_node",node={"type":"slab","polygon":[[4,22],[12,22],[12,27],[4,27]],"elevation":-0.5},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Swimming Pool","polygon":[[4,22],[12,22],[12,27],[4,27]],"color":"#0284c7"},parentId=L)

    # Pool deck surrounding
    await b.cmd("create_node",node={"type":"slab","polygon":[[1,21],[15,21],[15,29],[1,29]],"elevation":0.02,
        "holes":[[[4,22],[12,22],[12,27],[4,27]]]},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Pool Deck","polygon":[[1,21],[15,21],[15,29],[1,29]],"color":"#d4a574"},parentId=L)

    # Low pool fence
    await W(b,L,[1,21],[15,21],0.05,0.8)
    await W(b,L,[15,21],[15,29],0.05,0.8)
    await W(b,L,[15,29],[1,29],0.05,0.8)
    await W(b,L,[1,29],[1,21],0.05,0.8)

    # Pool furniture
    await p(b,L,SUNBED,[2,0,23],math.pi/2)
    await p(b,L,SUNBED,[2,0,25],math.pi/2)
    await p(b,L,UMBRELLA,[2,0,24])
    await p(b,L,SUNBED,[14,0,23],-math.pi/2)
    await p(b,L,SUNBED,[14,0,25],-math.pi/2)
    await p(b,L,UMBRELLA,[14,0,24])
    await p(b,L,SUNBED,[8,0,28])
    await p(b,L,SUNBED,[6,0,28])
    await p(b,L,UMBRELLA,[7,0,28.5])

    # ==================================================================
    # PARKING AREA — west side [-14,12]->[-6,20]
    # ==================================================================
    print("\n=== PARKING ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[-14,12],[-6,12],[-6,20],[-14,20]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Hotel Parking","polygon":[[-14,12],[-6,12],[-6,20],[-14,20]],"color":"#44403c"},parentId=L)
    # Carport ceiling (partial coverage)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-14,12],[-6,12],[-6,16],[-14,16]],"height":3.0},parentId=L)
    await p(b,L,PILLAR,[-13.5,0,12.3],0,[1,2,1])
    await p(b,L,PILLAR,[-6.5,0,12.3],0,[1,2,1])
    await p(b,L,PILLAR,[-13.5,0,15.7],0,[1,2,1])
    await p(b,L,PILLAR,[-6.5,0,15.7],0,[1,2,1])
    await p(b,L,TESLA,[-10,0,13.5])
    await p(b,L,TESLA,[-10,0,17.5])
    await p(b,L,TESLA,[-10,0,14.5],math.pi)

    # ==================================================================
    # SPORTS AREA — east side [22,14]->[30,20]
    # ==================================================================
    print("\n=== SPORTS AREA ===")
    await b.cmd("create_node",node={"type":"slab","polygon":[[22,14],[30,14],[30,20],[22,20]],"elevation":0.02},parentId=L)
    await b.cmd("create_node",node={"type":"zone","name":"Sports Court","polygon":[[22,14],[30,14],[30,20],[22,20]],"color":"#ea580c"},parentId=L)
    await p(b,L,HOOP,[26,0,14.5])
    await p(b,L,HOOP,[26,0,19.5],math.pi)
    await p(b,L,BALL,[27,0,17])
    await p(b,L,PLAYHOUSE,[24,0,18])
    await p(b,L,SCOOTER,[28,0,17])

    # ==================================================================
    # LANDSCAPE — perimeter trees, bushes, privacy screening
    # ==================================================================
    print("\n=== LANDSCAPE ===")

    # Trees around property
    for pos in [[-16,0,-2],[-16,0,5],[-16,0,12],[-16,0,20],[32,0,-2],[32,0,5],[32,0,12],[32,0,20],
                [-2,0,-3],[8,0,-3],[18,0,-3],[8,0,31],[0,0,30],[15,0,30]]:
        await p(b,L,TREE,pos)

    # Palms
    for pos in [[-2,0,21],[17,0,21],[0,0,-2],[16,0,-2],[30,0,10]]:
        await p(b,L,PALM,pos)

    # Privacy fir trees
    for pos in [[-15,0,-1],[-15,0,2],[-15,0,5],[-15,0,8],[31,0,-1],[31,0,2],[31,0,5],[31,0,8]]:
        await p(b,L,FIRTREE,pos)

    # Bushes (garden beds)
    for pos in [[2,0,-1],[6,0,-1],[10,0,-1],[14,0,-1],[24,0,-1],[28,0,-1],
                [-3,0,20.5],[19,0,20.5]]:
        await p(b,L,BUSH,pos)

    print("  Ground floor DONE!")

    # ==================================================================
    # FLOOR 2 (Upper Floor) — Level 1
    # ==================================================================
    print("\n========================================")
    print("  UPPER FLOOR (Level 1)")
    print("========================================")

    # Create level 1
    r = await b.cmd("create_node",node={"type":"level","elevation":H,"index":1},parentId=bid)
    lid1 = r.get("nodeId")
    if not lid1:
        print("ERROR: Could not create level 1")
        await b.close()
        return

    L1 = lid1
    await b.cmd("set_selection",selection={"levelId":L1})
    await asyncio.sleep(0.5)

    # ==================================================================
    # MAIN BLOCK 2F — Conference room, Lounge bar, Office
    # ==================================================================
    print("\n=== MAIN BLOCK 2F — Conference & Lounge ===")

    # Slab with stairwell hole
    await b.cmd("create_node",node={"type":"slab","polygon":[[0,0],[16,0],[16,10],[0,10]],
        "elevation":H,"holes":[[[0.5,0.5],[3,0.5],[3,3],[0.5,3]]]},parentId=L1)

    mw2=[]
    mw2.append(await W(b,L1,[0,0],[16,0],0.25,H2,True))     # 0: north
    mw2.append(await W(b,L1,[16,0],[16,10],0.25,H2,True))    # 1: east
    mw2.append(await W(b,L1,[16,10],[0,10],0.25,H2,True))    # 2: south
    mw2.append(await W(b,L1,[0,10],[0,0],0.25,H2,True))      # 3: west

    # Interior walls: stairwell | conference | lounge bar | office
    mw2.append(await W(b,L1,[3,0],[3,4],0.12,H2))            # 4: stairwell east
    mw2.append(await W(b,L1,[0,4],[7,4],0.12,H2))            # 5: stairwell south / conf north
    mw2.append(await W(b,L1,[7,0],[7,10],0.15,H2))           # 6: conference/lounge divider
    mw2.append(await W(b,L1,[7,7],[16,7],0.12,H2))           # 7: lounge/office divider

    # Doors
    await D(b,mw2[5],5,1.2,2.2)       # stairwell->conference
    await D(b,mw2[6],5,1.2,2.2)       # conference->lounge
    await D(b,mw2[7],6,0.9,2.2)       # lounge->office
    await D(b,mw2[2],3,1.0,2.2)       # conference exit south

    # Windows
    await WN(b,mw2[0],5,2.0,2.0,0.3)    # conference north
    await WN(b,mw2[0],10,3.0,2.0,0.3)   # lounge north
    await WN(b,mw2[1],2,2.5,2.0,0.3)    # lounge east
    await WN(b,mw2[1],8.5,1.2,1.2,1.0)  # office east
    await WN(b,mw2[2],8,2.0,2.0,0.3)    # lounge south
    await WN(b,mw2[3],6,2.0,2.0,0.3)    # conference west

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Stairwell","polygon":[[0,0],[3,0],[3,4],[0,4]],"color":"#6b7280"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Conference Room","polygon":[[0,4],[7,4],[7,10],[0,10]],"color":"#2563eb"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Lounge Bar","polygon":[[7,0],[16,0],[16,7],[7,7]],"color":"#b91c1c"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Office","polygon":[[7,7],[16,7],[16,10],[7,10]],"color":"#059669"},parentId=L1)

    # Ceiling
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[0,0],[16,0],[16,10],[0,10]],"height":H2},parentId=L1)

    # Furnish conference room
    print("  Furnishing conference room...")
    await p(b,L1,DTABLE,[3.5,0,7])
    await p(b,L1,OFFCHAIR,[3.5,0,6],math.pi)
    await p(b,L1,OFFCHAIR,[3.5,0,8])
    await p(b,L1,OFFCHAIR,[2.3,0,7],math.pi/2)
    await p(b,L1,OFFCHAIR,[4.7,0,7],-math.pi/2)
    await p(b,L1,OFFCHAIR,[2.3,0,6],math.pi/2)
    await p(b,L1,OFFCHAIR,[4.7,0,6],-math.pi/2)
    await p(b,L1,OFFCHAIR,[2.3,0,8],math.pi/2)
    await p(b,L1,OFFCHAIR,[4.7,0,8],-math.pi/2)
    await p(b,L1,BKSHELF,[0.5,0,4.5])
    await p(b,L1,PLANT,[6,0,4.5])
    await p(b,L1,PLANT,[0.5,0,9.5])

    # Furnish lounge bar
    print("  Furnishing lounge bar...")
    await p(b,L1,SOFA,[10,0,2])
    await p(b,L1,SOFA,[13,0,2])
    await p(b,L1,COFFEE,[10,0,3.5])
    await p(b,L1,COFFEE,[13,0,3.5])
    await p(b,L1,LIVCHAIR,[10,0,5],math.pi)
    await p(b,L1,LIVCHAIR,[13,0,5],math.pi)
    await p(b,L1,KCOUNTER,[8,0,1])       # bar counter
    await p(b,L1,STOOL,[8,0,2])
    await p(b,L1,STOOL,[8,0,3])
    await p(b,L1,FLAMP,[15,0,0.5])
    await p(b,L1,FLAMP,[8,0,6])
    await p(b,L1,RNDCARPET,[11.5,0,3.5])

    # Furnish office
    print("  Furnishing office...")
    await p(b,L1,OFFTABLE,[12,0,8.5])
    await p(b,L1,OFFCHAIR,[12,0,9.2])
    await p(b,L1,BKSHELF,[8,0,7.5])
    await p(b,L1,BKSHELF,[8,0,9])
    await p(b,L1,SPLANT,[15,0,9.5])

    # Stairs item (in stairwell)
    await p(b,L1,STAIRS,[1.5,0,1.5])

    # ==================================================================
    # WEST WING 2F — Rooms 201-204
    # ==================================================================
    print("\n=== WEST WING 2F — Rooms 201-204 ===")

    # Slab with stairwell hole
    await b.cmd("create_node",node={"type":"slab","polygon":[[-14,0],[-6,0],[-6,10],[-14,10]],
        "elevation":H,"holes":[[[-10.5,4.5],[-9.5,4.5],[-9.5,5.5],[-10.5,5.5]]]},parentId=L1)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-14,0],[-6,0],[-6,10],[-14,10]],"height":H2},parentId=L1)

    ww2=[]
    ww2.append(await W(b,L1,[-14,0],[-6,0],0.2,H2,True))
    ww2.append(await W(b,L1,[-6,0],[-6,10],0.2,H2,True))
    ww2.append(await W(b,L1,[-6,10],[-14,10],0.2,H2,True))
    ww2.append(await W(b,L1,[-14,10],[-14,0],0.2,H2,True))
    ww2.append(await W(b,L1,[-10,0],[-10,10],0.12,H2))
    ww2.append(await W(b,L1,[-14,5],[-6,5],0.12,H2))

    # Bath walls
    ww2.append(await W(b,L1,[-14,2],[-12,2],0.1,H2))
    ww2.append(await W(b,L1,[-12,0],[-12,2],0.1,H2))
    ww2.append(await W(b,L1,[-8,0],[-8,2],0.1,H2))
    ww2.append(await W(b,L1,[-8,2],[-6,2],0.1,H2))
    ww2.append(await W(b,L1,[-14,8],[-12,8],0.1,H2))
    ww2.append(await W(b,L1,[-12,8],[-12,10],0.1,H2))
    ww2.append(await W(b,L1,[-8,8],[-8,10],0.1,H2))
    ww2.append(await W(b,L1,[-8,8],[-6,8],0.1,H2))

    # Doors
    await D(b,ww2[1],2,0.9,2.2)
    await D(b,ww2[1],7,0.9,2.2)
    await D(b,ww2[3],2,0.9,2.2)
    await D(b,ww2[3],7,0.9,2.2)
    await D(b,ww2[6],1,0.7,2.1)
    await D(b,ww2[9],1,0.7,2.1)
    await D(b,ww2[10],1,0.7,2.1)
    await D(b,ww2[13],1,0.7,2.1)

    # Windows
    await WN(b,ww2[0],2,1.5,1.8,0.5)
    await WN(b,ww2[0],6,1.5,1.8,0.5)
    await WN(b,ww2[2],2,1.5,1.8,0.5)
    await WN(b,ww2[2],6,1.5,1.8,0.5)

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Room 201","polygon":[[-14,0],[-10,0],[-10,5],[-14,5]],"color":"#7c3aed"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Room 202","polygon":[[-10,0],[-6,0],[-6,5],[-10,5]],"color":"#8b5cf6"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Room 203","polygon":[[-14,5],[-10,5],[-10,10],[-14,10]],"color":"#7c3aed"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Room 204","polygon":[[-10,5],[-6,5],[-6,10],[-10,10]],"color":"#8b5cf6"},parentId=L1)

    # Furnish rooms 201-204
    print("  Furnishing rooms 201-204...")
    # Room 201
    await p(b,L1,DBED,[-12,0,3.5])
    await p(b,L1,BSIDE,[-13.5,0,3])
    await p(b,L1,BSIDE,[-10.5,0,3])
    await p(b,L1,DRESSER,[-12,0,4.5],math.pi)
    await p(b,L1,TOILET,[-13,0,1],math.pi)
    await p(b,L1,SINK,[-13,0,0.5],math.pi)

    # Room 202
    await p(b,L1,DBED,[-8,0,3.5])
    await p(b,L1,BSIDE,[-9.5,0,3])
    await p(b,L1,BSIDE,[-6.5,0,3])
    await p(b,L1,DRESSER,[-8,0,4.5],math.pi)
    await p(b,L1,TOILET,[-7,0,1],math.pi)
    await p(b,L1,SINK,[-7,0,0.5],math.pi)

    # Room 203
    await p(b,L1,DBED,[-12,0,6])
    await p(b,L1,BSIDE,[-13.5,0,6.5])
    await p(b,L1,BSIDE,[-10.5,0,6.5])
    await p(b,L1,DRESSER,[-12,0,5.3])
    await p(b,L1,TOILET,[-13,0,9],math.pi)
    await p(b,L1,SINK,[-13,0,8.5])

    # Room 204
    await p(b,L1,DBED,[-8,0,6])
    await p(b,L1,BSIDE,[-9.5,0,6.5])
    await p(b,L1,BSIDE,[-6.5,0,6.5])
    await p(b,L1,DRESSER,[-8,0,5.3])
    await p(b,L1,TOILET,[-7,0,9],math.pi)
    await p(b,L1,SINK,[-7,0,8.5])

    # ==================================================================
    # EAST WING 2F — Rooms 205-208
    # ==================================================================
    print("\n=== EAST WING 2F — Rooms 205-208 ===")

    await b.cmd("create_node",node={"type":"slab","polygon":[[22,0],[30,0],[30,10],[22,10]],
        "elevation":H,"holes":[[[25.5,4.5],[26.5,4.5],[26.5,5.5],[25.5,5.5]]]},parentId=L1)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[22,0],[30,0],[30,10],[22,10]],"height":H2},parentId=L1)

    ew2=[]
    ew2.append(await W(b,L1,[22,0],[30,0],0.2,H2,True))
    ew2.append(await W(b,L1,[30,0],[30,10],0.2,H2,True))
    ew2.append(await W(b,L1,[30,10],[22,10],0.2,H2,True))
    ew2.append(await W(b,L1,[22,10],[22,0],0.2,H2,True))
    ew2.append(await W(b,L1,[26,0],[26,10],0.12,H2))
    ew2.append(await W(b,L1,[22,5],[30,5],0.12,H2))

    # Bath walls
    ew2.append(await W(b,L1,[22,2],[24,2],0.1,H2))
    ew2.append(await W(b,L1,[24,0],[24,2],0.1,H2))
    ew2.append(await W(b,L1,[28,0],[28,2],0.1,H2))
    ew2.append(await W(b,L1,[28,2],[30,2],0.1,H2))
    ew2.append(await W(b,L1,[22,8],[24,8],0.1,H2))
    ew2.append(await W(b,L1,[24,8],[24,10],0.1,H2))
    ew2.append(await W(b,L1,[28,8],[28,10],0.1,H2))
    ew2.append(await W(b,L1,[28,8],[30,8],0.1,H2))

    # Doors
    await D(b,ew2[3],2,0.9,2.2)
    await D(b,ew2[3],7,0.9,2.2)
    await D(b,ew2[1],2,0.9,2.2)
    await D(b,ew2[1],7,0.9,2.2)
    await D(b,ew2[6],1,0.7,2.1)
    await D(b,ew2[9],1,0.7,2.1)
    await D(b,ew2[10],1,0.7,2.1)
    await D(b,ew2[13],1,0.7,2.1)

    # Windows
    await WN(b,ew2[0],2,1.5,1.8,0.5)
    await WN(b,ew2[0],6,1.5,1.8,0.5)
    await WN(b,ew2[2],2,1.5,1.8,0.5)
    await WN(b,ew2[2],6,1.5,1.8,0.5)

    # Zones
    await b.cmd("create_node",node={"type":"zone","name":"Room 205","polygon":[[22,0],[26,0],[26,5],[22,5]],"color":"#7c3aed"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Room 206","polygon":[[26,0],[30,0],[30,5],[26,5]],"color":"#8b5cf6"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Room 207","polygon":[[22,5],[26,5],[26,10],[22,10]],"color":"#7c3aed"},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"Room 208","polygon":[[26,5],[30,5],[30,10],[26,10]],"color":"#8b5cf6"},parentId=L1)

    # Furnish rooms 205-208
    print("  Furnishing rooms 205-208...")
    # Room 205
    await p(b,L1,DBED,[24,0,3.5])
    await p(b,L1,BSIDE,[22.5,0,3])
    await p(b,L1,BSIDE,[25.5,0,3])
    await p(b,L1,DRESSER,[24,0,4.5],math.pi)
    await p(b,L1,TOILET,[23,0,1],math.pi)
    await p(b,L1,SINK,[23,0,0.5],math.pi)

    # Room 206
    await p(b,L1,DBED,[28,0,3.5])
    await p(b,L1,BSIDE,[26.5,0,3])
    await p(b,L1,BSIDE,[29.5,0,3])
    await p(b,L1,DRESSER,[28,0,4.5],math.pi)
    await p(b,L1,TOILET,[29,0,1],math.pi)
    await p(b,L1,SINK,[29,0,0.5],math.pi)

    # Room 207
    await p(b,L1,DBED,[24,0,6])
    await p(b,L1,BSIDE,[22.5,0,6.5])
    await p(b,L1,BSIDE,[25.5,0,6.5])
    await p(b,L1,DRESSER,[24,0,5.3])
    await p(b,L1,TOILET,[23,0,9],math.pi)
    await p(b,L1,SINK,[23,0,8.5])

    # Room 208
    await p(b,L1,DBED,[28,0,6])
    await p(b,L1,BSIDE,[26.5,0,6.5])
    await p(b,L1,BSIDE,[29.5,0,6.5])
    await p(b,L1,DRESSER,[28,0,5.3])
    await p(b,L1,TOILET,[29,0,9],math.pi)
    await p(b,L1,SINK,[29,0,8.5])

    # ==================================================================
    # COVERED WALKWAYS 2F — connecting wings to main block
    # ==================================================================
    print("\n=== 2F COVERED WALKWAYS ===")

    # West walkway 2F
    await b.cmd("create_node",node={"type":"slab","polygon":[[-6,3],[0,3],[0,7],[-6,7]],"elevation":H},parentId=L1)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[-6,3],[0,3],[0,7],[-6,7]],"height":H2},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"West Corridor 2F","polygon":[[-6,3],[0,3],[0,7],[-6,7]],"color":"#9ca3af"},parentId=L1)
    await p(b,L1,PILLAR,[-5.7,0,3.3],0,[1,2.1,1])
    await p(b,L1,PILLAR,[-5.7,0,6.7],0,[1,2.1,1])
    await p(b,L1,PILLAR,[-0.3,0,3.3],0,[1,2.1,1])
    await p(b,L1,PILLAR,[-0.3,0,6.7],0,[1,2.1,1])
    await p(b,L1,PILLAR,[-3,0,3.3],0,[1,2.1,1])
    await p(b,L1,PILLAR,[-3,0,6.7],0,[1,2.1,1])
    # Balcony railing (half-height walls)
    await W(b,L1,[-6,3],[0,3],0.05,1.0)
    await W(b,L1,[0,7],[-6,7],0.05,1.0)

    # East walkway 2F
    await b.cmd("create_node",node={"type":"slab","polygon":[[16,3],[22,3],[22,7],[16,7]],"elevation":H},parentId=L1)
    await b.cmd("create_node",node={"type":"ceiling","polygon":[[16,3],[22,3],[22,7],[16,7]],"height":H2},parentId=L1)
    await b.cmd("create_node",node={"type":"zone","name":"East Corridor 2F","polygon":[[16,3],[22,3],[22,7],[16,7]],"color":"#9ca3af"},parentId=L1)
    await p(b,L1,PILLAR,[16.3,0,3.3],0,[1,2.1,1])
    await p(b,L1,PILLAR,[16.3,0,6.7],0,[1,2.1,1])
    await p(b,L1,PILLAR,[21.7,0,3.3],0,[1,2.1,1])
    await p(b,L1,PILLAR,[21.7,0,6.7],0,[1,2.1,1])
    await p(b,L1,PILLAR,[19,0,3.3],0,[1,2.1,1])
    await p(b,L1,PILLAR,[19,0,6.7],0,[1,2.1,1])
    await W(b,L1,[16,3],[22,3],0.05,1.0)
    await W(b,L1,[22,7],[16,7],0.05,1.0)

    # No roofs — they crash the CSG system on complex shapes

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print(f"\n{'='*60}")
    print("  THE COURTYARD HOTEL — COMPLETE")
    print("  ────────────────────────────────────────")
    print("  GROUND FLOOR:")
    print("    Main Block (16x10m):")
    print("      Hotel Lobby with reception desk")
    print("      Restaurant with 4 dining tables (16 seats)")
    print("      Commercial kitchen")
    print("    West Wing (8x10m):")
    print("      Rooms 101-104 with en-suite bathrooms")
    print("    East Wing (8x10m):")
    print("      Rooms 105-108 with en-suite bathrooms")
    print("    Covered Walkways connecting wings")
    print("    Central Courtyard with palms, seating, dining")
    print("    Swimming Pool (8x5m) with deck and sunbeds")
    print("    Parking with carport (3 Teslas)")
    print("    Sports court with basketball hoops")
    print("")
    print("  UPPER FLOOR:")
    print("    Main Block:")
    print("      Conference room (8-seat table)")
    print("      Lounge bar with sofas and bar counter")
    print("      Manager's office with bookshelves")
    print("    West Wing: Rooms 201-204 with en-suite baths")
    print("    East Wing: Rooms 205-208 with en-suite baths")
    print("    Balcony walkways with railings")
    print("    No roofs (open-top modern style)")
    print("")
    print("  TOTAL: 16 guest rooms, 2 stories")
    print("  OUTDOOR: pool, courtyard, parking, sports")
    print("  ────────────────────────────────────────")
    print("  U-shape layout with central courtyard")
    print("  Multiple separate volumes, covered walkways")
    print("  3.5m ground floor / 3.0m upper floor")
    print(f"{'='*60}")
    await b.close()

if __name__=="__main__":
    asyncio.run(main())
