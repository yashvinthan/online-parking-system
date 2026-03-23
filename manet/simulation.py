import math
import random

# ══════════════════════════════════════════════════════════════════════════════
#  Real-Life Parking Simulation
#
#  Canvas: 800 × 600 px
#
#  LAYOUT (y increases DOWNWARD):
#
#   y= 55   ┌───────────────── SPOT ROW 3 ─────────────────┐  cy=55
#   y=105   └─── AISLE 3 (y=105) ───────────────────────────┘
#   y=145   ┌───────────────── SPOT ROW 2 ─────────────────┐  cy=145
#   y=205   └─── AISLE 2 (y=205) ───────────────────────────┘
#   y=245   ┌───────────────── SPOT ROW 1 ─────────────────┐  cy=245
#   y=305   └─── AISLE 1 (y=305) ───────────────────────────┘
#   y=345   ┌───────────────── SPOT ROW 0 ─────────────────┐  cy=345
#   y=405   └─── AISLE 0 (y=405) ───────────────────────────┘
#   y=480   ════════════════ MAIN ROAD ══════════════════════
#         EXIT (x=60)                 ENTRANCE (x=740)
#
#  Entry lane  x=740  (right edge)
#  Exit  lane  x=60   (left  edge)
#
#  Car path IN :  spawn(740,640) → up x=740 → left on aisle → up into spot
#  Car path OUT:  down from spot → left on aisle → down x=60 → despawn
# ══════════════════════════════════════════════════════════════════════════════

SPEED       = 3.0      # px per tick  — slow = realistic
REACH       = SPEED    # "arrived" threshold

ENTRY_X     = 740
EXIT_X      = 60
SPAWN_Y     = 640      # below canvas
MAIN_LANE_Y = 480      # main horizontal road

AISLE_Y   = [405, 305, 205, 105]   # 4 aisles; index 0 = closest to main road
SPOT_CY   = [345, 245, 145,  55]   # spot centres; SPOT_CY[r] < AISLE_Y[r] ✓
SPOT_COLS = [160, 270, 380, 490, 600, 710]  # 6 columns
SPOT_W, SPOT_H = 80, 70


class Spot:
    def __init__(self, sid, cx, cy, row_idx):
        self.id          = sid
        self.x           = cx
        self.y           = cy
        self.row_idx     = row_idx
        self.occupied_by = None


def _entry_path(spot):
    aisle_y = AISLE_Y[spot.row_idx]
    return [
        (ENTRY_X, aisle_y),  # 1. drive UP entry lane to the correct aisle level
        (spot.x,  aisle_y),  # 2. turn LEFT along aisle to spot column
        (spot.x,  spot.y),   # 3. pull UP into spot
    ]


def _exit_path(spot):
    aisle_y = AISLE_Y[spot.row_idx]
    return [
        (spot.x,  aisle_y),   # 1. reverse back to aisle
        (EXIT_X,  aisle_y),   # 2. drive LEFT along aisle to exit lane
        (EXIT_X,  SPAWN_Y),   # 3. drive DOWN exit lane → off canvas
    ]


# ─── Car ──────────────────────────────────────────────────────────────────────

class Node:
    """States: ENTERING  PARKED  LEAVING  WAITING"""

    def __init__(self, node_id, spawn_offset_y=0):
        self.id   = node_id
        self.seq_num = 1
        self.routing_table      = {}
        self.broadcast_ids_seen = set()
        self.messages_logs      = []

        self.x           = ENTRY_X
        self.y           = SPAWN_Y + spawn_offset_y   # start below canvas
        self.state       = "ENTERING"
        self.waypoints   = []
        self.target_spot = None
        self.park_timer  = 0

    def to_dict(self):
        return {"id": self.id, "x": round(self.x, 1),
                "y": round(self.y, 1), "state": self.state}

    def assign_spot(self, spot):
        spot.occupied_by = self.id
        self.target_spot = spot
        self.waypoints   = _entry_path(spot)
        self.state       = "ENTERING"

    def _move_toward(self, tx, ty):
        """Pure waypoint move; returns True when arrived."""
        dx, dy = tx - self.x, ty - self.y
        dist   = math.hypot(dx, dy)
        if dist <= REACH:
            self.x, self.y = tx, ty
            return True
        self.x += dx / dist * SPEED
        self.y += dy / dist * SPEED
        return False

    def _follow_waypoints(self):
        if not self.waypoints:
            return True
        tx, ty = self.waypoints[0]
        if self._move_toward(tx, ty):
            self.waypoints.pop(0)
        return len(self.waypoints) == 0

    def update(self, spots):
        if self.state == "ENTERING":
            if self._follow_waypoints():
                if self.target_spot:
                    self.x      = self.target_spot.x
                    self.y      = self.target_spot.y
                    self.state  = "PARKED"
                    self.park_timer = random.randint(120, 280)

        elif self.state == "PARKED":
            self.park_timer -= 1
            if self.park_timer <= 0:
                spot = self.target_spot
                self.waypoints   = _exit_path(spot)
                spot.occupied_by = None
                self.target_spot = None
                self.state       = "LEAVING"

        elif self.state == "LEAVING":
            self._follow_waypoints()      # removal handled by simulation

        elif self.state == "WAITING":
            free = [s for s in spots if s.occupied_by is None]
            if free:
                self.assign_spot(random.choice(free))


# ═══════════════════════════════════════════════════════════════════════════════
#  AODVSimulation
# ═══════════════════════════════════════════════════════════════════════════════

class AODVSimulation:
    def __init__(self, num_nodes=10, wifi_range=150, max_x=800, max_y=600):
        self.wifi_range   = wifi_range
        self.max_x        = max_x
        self.max_y        = max_y
        self.tick         = 0
        self.events       = []
        self.target_nodes = num_nodes
        self.next_id      = 1
        self.nodes        = {}

        # 6 cols × 4 rows = 24 spots
        self.spots = []
        idx = 1
        for ri, cy in enumerate(SPOT_CY):
            for cx in SPOT_COLS:
                self.spots.append(Spot(f"P{idx}", cx, cy, ri))
                idx += 1

    def _free(self):
        return [s for s in self.spots if s.occupied_by is None]

    def _spawn(self, offset_y=0):
        nid = f"V-{self.next_id}"
        self.next_id += 1
        car = Node(nid, spawn_offset_y=offset_y)
        free = self._free()
        if free:
            car.assign_spot(random.choice(free))
        else:
            car.waypoints = []
            car.state     = "WAITING"
        self.nodes[nid] = car
        return car

    # ── AODV ──────────────────────────────────────────────────────────────── #

    def add_event(self, etype, msg):
        msg['event_type'] = etype
        msg['tick'] = self.tick
        self.events.append(msg)

    def get_neighbors(self, nid):
        n = self.nodes[nid]
        return [k for k, o in self.nodes.items()
                if k != nid and math.hypot(o.x-n.x, o.y-n.y) <= self.wifi_range]

    def initiate_rreq(self, src, dest):
        if src not in self.nodes: return
        bid = f"{src}_{self.tick}"
        self.add_event('RREQ', {'src': src, 'dest': dest,
                                'broadcast_id': bid, 'info': f"RREQ {src}→{dest}"})
        self.nodes[src].broadcast_ids_seen.add(bid)
        for nb in self.get_neighbors(src):
            self._fwd_rreq(nb, src, dest, bid, 1)

    def _fwd_rreq(self, cur, src, dest, bid, hops):
        if cur not in self.nodes: return
        n = self.nodes[cur]
        if bid in n.broadcast_ids_seen: return
        n.broadcast_ids_seen.add(bid)
        n.routing_table[src] = {'next_hop': src, 'hops': hops}
        if cur == dest:
            self._send_rrep(dest, src, 0); return
        for nb in self.get_neighbors(cur):
            self._fwd_rreq(nb, src, dest, bid, hops + 1)

    def _send_rrep(self, src, dest, hops):
        self.add_event('RREP', {'src': src, 'dest': dest,
                                'info': f"RREP {src}→{dest}"})
        if src not in self.nodes: return
        n = self.nodes[src]
        if dest in n.routing_table:
            nh = n.routing_table[dest]['next_hop']
            if nh in self.nodes:
                self._send_rrep(nh, dest, hops + 1)

    def send_data(self, src, dest, msg):
        if src not in self.nodes or dest not in self.nodes: return
        sn = self.nodes[src]
        if dest in sn.routing_table:
            nh = sn.routing_table[dest]['next_hop']
            if nh in self.get_neighbors(src):
                self.add_event('DATA', {'src': src, 'dest': dest,
                                        'current': src, 'next_hop': nh,
                                        'info': f"Msg: {msg}"})
                self._fwd_data(nh, dest, msg, src)
            else:
                del sn.routing_table[dest]
                self.add_event('RERR', {'src': src, 'broken_link': nh,
                                        'info': "Link broken"})
                self.initiate_rreq(src, dest)
        else:
            self.initiate_rreq(src, dest)

    def _fwd_data(self, cur, dest, data, orig):
        if cur == dest:
            self.add_event('DATA_DELIVERED', {'src': orig, 'dest': dest,
                                               'info': f"Delivered: {data}"}); return
        n = self.nodes.get(cur)
        if not n: return
        if dest in n.routing_table:
            nh = n.routing_table[dest]['next_hop']
            if nh in self.get_neighbors(cur):
                self.add_event('DATA_FORWARD', {'src': orig, 'dest': dest,
                                                 'current': cur, 'next_hop': nh})
                self._fwd_data(nh, dest, data, orig)

    # ── main step ─────────────────────────────────────────────────────────── #

    def step(self):
        self.tick += 1

        # Remove cars that have left the canvas
        for nid in list(self.nodes.keys()):
            n = self.nodes[nid]
            if n.state == "LEAVING" and n.y >= SPAWN_Y - 5:
                del self.nodes[nid]

        # Spawn a new car every 30 ticks
        if len(self.nodes) < self.target_nodes and self.tick % 30 == 0:
            self._spawn()

        # Give WAITING cars a spot if one opened
        for node in list(self.nodes.values()):
            if node.state == "WAITING":
                free = self._free()
                if free:
                    node.assign_spot(random.choice(free))

        # Move all cars
        for node in list(self.nodes.values()):
            node.update(self.spots)

        # Build frame output
        nodes_data = [n.to_dict() for n in self.nodes.values()]
        keys = list(self.nodes.keys())
        links = []
        for i, a in enumerate(keys):
            na = self.nodes[a]
            for b in keys[i + 1:]:
                nb = self.nodes[b]
                if math.hypot(na.x - nb.x, na.y - nb.y) <= self.wifi_range:
                    links.append({"source": a, "target": b})

        if random.random() < 0.05 and len(self.nodes) > 1:
            ids = list(self.nodes.keys())
            s, d = random.sample(ids, 2)
            self.send_data(s, d, random.choice(
                ["Spot open?", "Slot reserved", "Leaving now", "MANET ping"]))

        result = {
            "tick":   self.tick,
            "nodes":  nodes_data,
            "links":  links,
            "events": list(self.events),
            "spots": [{"id": sp.id, "x": sp.x, "y": sp.y,
                       "occupied": sp.occupied_by is not None}
                      for sp in self.spots],
        }
        self.events.clear()
        return result

    def simulate_scenario(self, steps=200):
        # Spawn initial cars one at a time staggered by 50 ticks each
        # so the first few frames show cars entering cleanly one-by-one
        initial = min(6, self.target_nodes)
        for i in range(initial):
            car = self._spawn(offset_y=i * 60)
        history = []
        for _ in range(steps):
            history.append(self.step())
        return history
