"""The simulation: state and the yearly step."""
import time
import numpy as np

from .params import *  # noqa: F401,F403
from .geo import *  # noqa: F401,F403
from .land import LandMixin
from .economy import EconomyMixin
from .settlement import SettlementMixin
from .dragons import DragonsMixin
from .culture import CultureMixin
from .states import StatesMixin
from .war import WarMixin
from .technology import TechnologyMixin
from .diagnostics import DiagnosticsMixin
from .cities import CitiesMixin
from .render import *  # noqa: F401,F403


class Sim(CitiesMixin, LandMixin, EconomyMixin, SettlementMixin, DragonsMixin, CultureMixin, StatesMixin, WarMixin, TechnologyMixin, DiagnosticsMixin):
    def __init__(self, world, seed=1, years=6000, frame_every=10, out=None,
                 homelands="continents", peoples=None, start_pool=0.0,
                 starts=3, start_vary=0.05, drift=0.06, cluster_km=0.0,
                 settle_drift=0.03, size_food="kleiber", start_mode="wander",
                 wander_steps=2000, off=(), shuffle_sites=False,
                 sites="sites.json"):
        self.W = W = world
        self.on = set(FEATURES) - set(off)
        self.homelands = homelands
        self.start_pool = start_pool
        self.starts = starts
        self.start_vary = start_vary
        self.drift = drift
        self.cluster_km = cluster_km
        self.settle_drift = settle_drift
        self.start_mode = start_mode
        self.wander_steps = wander_steps
        self.shuffle_sites = shuffle_sites
        self.sites_file = sites
        self.size_food = size_food
        self.vary = 0.0
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.years = years
        self.frame_every = frame_every
        self.out = out
        P = self.P = peoples
        self.nP = nP = len(P)
        self.keys = [p["key"] for p in P]
        self.colors = np.array([p["color"] for p in P], np.uint8)
        self.pT = np.array([[p.get(t, 0.5) for t in TRAITS] for p in P])
        self.pr = np.array([p["r"] for p in P], float)
        self.paff = np.array([[p["affinity"].get(b, 1.0) for b in BIOMES]
                              for p in P])
        # body size: combat worth per head relative to a human. With
        # size_food="kleiber" each head also eats size**0.75 humans' food,
        # so the land carries fewer large bodies.
        self.psize = np.array([p.get("size", 1.0) for p in P], float)
        self.pwet = np.array([p.get("wet", 0.0) for p in P], float)
        self.phost = np.array([bool(p.get("dragon_host", False))
                               for p in P])
        self.phardy = np.array([p.get("hardy", 1.0) for p in P], float)
        self.pfort = np.array([p.get("fortress", 0.0) for p in P], float)
        # city threshold per people, in heads: CITY_POP food-equivalents,
        # times the roster's optional `city` factor (>1 = founds fewer)
        self.pcity = None
        self.peat = np.array([p.get("eat", p.get("size", 1.0) ** 0.75
                                    if size_food == "kleiber" else 1.0)
                              for p in P], float)

        # lineages: one row each; traits and technology live here
        nT = len(TRAITS)
        self.LT = np.zeros((MAXL, nT))
        self.Lr = np.zeros(MAXL)
        self.Laff = np.ones((MAXL, len(BIOMES)))
        self.Lbest = np.ones(MAXL)       # best biome affinity (cached)
        # ltab(): K2's per-lineage tables and the version that invalidates
        # them (bumped by every write to agri, metal or domlv)
        self.lver, self._ltab_ver, self._ltab_n = 0, -1, 0
        self.Lpeople = -np.ones(MAXL, int)
        self.Lparent = -np.ones(MAXL, int)
        self.Lparent2 = -np.ones(MAXL, int)   # second parent (fusion)
        self.Lfate = {}                        # absorbed/fused into
        self.fuse_age, self.lin_events, self.lin_pairs = {}, [], []
        self.Lfounded = np.zeros(MAXL, int)
        self.Lended = -np.ones(MAXL, int)
        self.Lhow = []
        self.Lcol = np.zeros((MAXL, 3), np.uint8)
        self.Lpeak = np.zeros(MAXL)
        self.Lseen = {}
        self.Pblk = [set() for _ in P]   # regions each people has held
        self.agri = np.zeros(MAXL)
        self.metal = np.zeros(MAXL)
        self.sail = np.zeros(MAXL)
        self.fishing = np.zeros(MAXL)
        self.craft = np.zeros(MAXL)
        self.ore_has = np.zeros((MAXL, 3), bool)
        self.admin = np.zeros(MAXL)
        self.bronze = np.zeros(MAXL, bool)
        self.iron = np.zeros(MAXL, bool)
        self.steel = np.zeros(MAXL, bool)
        # supply: stages known (kept for good) and ticks each in-use stage
        # has gone without its ores or cities
        self.known = np.zeros((MAXL, 3), bool)
        self.lack = np.zeros((MAXL, 3), int)
        self.nL = 0
        for t, k in TI.items():           # column views, kept in sync
            setattr(self, TRAIT_ATTR[t], self.LT[:, k])
        self.pX = np.array([[p.get(t, 0.5) for t in XTRAITS] for p in P])
        self.pvar = np.array([p.get("variance", 1.0) for p in P])
        self.plife = np.array([p.get("lifespan", 1.0) for p in P])
        self.LX = np.full((MAXL, len(XTRAITS)), 0.5)
        self.hier, self.pati = self.LX[:, 0], self.LX[:, 1]
        self.conf, self.pros = self.LX[:, 2], self.LX[:, 3]
        self.dom = self.LX[:, 4]
        self.crafts = self.LX[:, 5]
        self.xrng = np.random.default_rng(80_000 + seed)
        self.prng = np.random.default_rng(85_000 + seed)
        self.srng = np.random.default_rng(89_000 + seed)
        self.rrng = np.random.default_rng(91_000 + seed)   # ruler draws
        self.crng2 = np.random.default_rng(93_000 + seed)  # city culture
        nK = len(TRAITS) + len(XTRAITS)
        self.CE = np.full((CITY_MAX, nK), 0.5)   # city elites
        self.CM = np.full((CITY_MAX, nK), 0.5)   # city commons
        self.Chome = -np.ones(CITY_MAX, int)     # plurality lineage
        self.cc_on = "city_culture" in self.on
        self.dom_on = "dominion" in self.on
        # `food_flow` works through dominion's extraction
        self.ff_on = self.dom_on and "food_flow" in self.on
        self.uc_on = "urban_city" in self.on
        self._pt = {}
        self.Cmem = np.zeros((CITY_MAX, 5))       # war, trade, hard, raid, revolt
        self.CH = np.zeros((CITY_MAX, nK))        # commons' own history
        self.Ctnear = np.zeros(CITY_MAX)          # local trade reach
        self.Cwcap = np.zeros(CITY_MAX)           # capital's share of influence
        self.Cwown = np.zeros(CITY_MAX)           # own state's share
        self.city_rows, self.city_gap_rows, self.city_trait_rows = [], [], []
        self.Cadm = np.zeros(CITY_MAX)            # city administration
        self.ca_on = self.cc_on and "city_admin" in self.on
        self.rt = "ruler_traits" in self.on and "rulers" in self.on
        self.n_dyn = 0
        self.roadt = np.zeros(MAXL)          # road engineering
        self.Lsup = np.full(MAXL, SUP0)     # superiority
        self.Lapp = np.ones(MAXL)           # appetite for goods
        self.sup_win, self.sup_loss = {}, {}  # sup_exp: pid -> this tick
        self.psup = np.array([p.get("superiority", SUP0) for p in P])
        self.Lpart = np.full(MAXL, PART0)   # partibility (rulers)
        self.p_output = {}                  # pid -> precious output
        self.Lcolony = -np.ones(MAXL, int)  # state that sent a colony
        self.colony_lin = {}                # (state, landmass) -> lineage
        self.posts = {}                     # (lo, hi) -> (owner, city, yr)
        self.waste = np.ones(world.N)       # devastation: capacity share
        self.pdist = {}     # travel_reach: pid -> [sources, graph version,
                            # land distances, coast km, any coastal seat,
                            # sea factor, distances]
        self.seats = {}     # provinces: pid -> provincial seat cells
        self.held = {}      # provinces: city -> (pid, year taken)
        self.rule_key = -np.ones(world.N, int)  # acc_cross: ruler, subject
        self.rule_since = np.zeros(world.N)     # acc_cross: since (year)
        self.ruler_log = []
        self.n_ruler = 0

        N = W.N
        self.pcity = CITY_POP * np.array([p.get("city", 1.0) for p in P]) / \
            self.peat
        self.Kcap = np.full(N, np.inf)    # city size caps (food-equivalent)
        self.blk = (W.row // BLOCK) * (NX // BLOCK + 1) + W.col // BLOCK
        self.pop = np.zeros(N)
        self.cul = -np.ones(N, int)       # people per cell
        self.lin = -np.ones(N, int)       # lineage per cell
        self.drought = np.ones(N)
        self.Kcell = np.ones(N)
        # structural state
        self.land = np.ones(N)            # land condition (farm multiplier)
        self.herding = np.zeros(N, bool)  # cell lives by herding
        self.moist = np.zeros(N)          # climate moisture anomaly (sd)
        self.cm = np.ones((4, N))         # climate multipliers: rain-fed
                                          # farming, irrigation, forage, herd
        self.eco_tgt = -np.ones(N, int)   # biome a cell is shifting toward
        self.eco_f = np.zeros(N)
        self.events_abrupt = []
        self.n_avulsions = 0
        self.famine_movers = 0.0
        self._great_dry = -9999
        self.mcul = -np.ones(N, int)      # minority people per cell
        self.mlin = -np.ones(N, int)
        self.mpop = np.zeros(N)
        self.mcap = np.zeros(N, bool)     # minority capped (merchants)
        self.rul_c = -np.ones(N, int)     # ruling people of the cell's state
        self.rul_est = np.zeros(N)        # its state's establishment
        self.ext_x = np.zeros(N)          # extraction rate on subjects
        self.ext_in = np.zeros(N)         # food received (ruling people)
        self.new_state_v2()
        self.imm = np.zeros(N)            # plague immunity
        self.road = np.zeros(N)           # road stock 0-1
        self.roadq = np.ones(N)           # road quality (`road_tech`)
        self.imp = np.zeros(N)            # improvements 0-1
        self.salt = np.zeros(N)           # salt on irrigated land 0-1
        self.hard = np.zeros(N)           # hardship this tick (0/1)
        self.raided = np.zeros(N)         # raided or raiding this tick
        self.revolted = np.zeros(N)       # state lost cities to revolt
        self.pevent = {}                  # pid -> spike years this tick
        self.Lgen_next = np.zeros(MAXL)   # year of next generation turnover
        self.Lraidm = np.zeros(MAXL)      # raid memory per lineage
        self.Lwarm = np.zeros(MAXL)       # war memory per lineage
        self.Lhardm = np.zeros(MAXL)      # hardship memory per lineage
        self.Ltradem = np.zeros(MAXL)     # trade volume, smoothed
        self.Lchurn = np.zeros(MAXL)      # cultural churn per century
        # trait change from experience since the last Price snapshot
        self.Lexp = np.zeros((MAXL, len(TRAITS) + len(XTRAITS)))
        # ...and from following rulers (`ruler_traits`)
        self.Lrul = np.zeros((MAXL, len(TRAITS) + len(XTRAITS)))
        self.vassal = {}                  # vassal pid -> overlord pid
        self.price_rows = []
        self.price_snap = None
        self.n_revolts = 0
        self.cnt = {}                     # event counts this tick
        self._pretender = False
        # climate has its own random stream: the same seed gives the same
        # climate history whatever else is switched on
        self.crng = np.random.default_rng(50_000 + seed)
        self.climate_setup()
        # dragons have their own random stream too
        self.drng = np.random.default_rng(70_000 + seed)
        self.d_by_pid = {}
        self.dragon_kills = np.zeros(nP)
        self.dragon_setup()
        self.sites_setup()
        self.tick = 0
        self.year = 0
        self.events = []
        self.firsts = set()
        self.p_seen = np.zeros(nP, bool)
        self.p_extinct = np.zeros(nP, bool)
        self.contact_seen = np.zeros((nP, nP), bool)
        self.trade_seen = np.zeros((nP, nP), bool)

        self.cities = {}            # cell -> record (active)
        self.city_hist = []         # all records
        self.city_years = np.zeros(N)
        self.city_peak = np.zeros(N)
        self.polities = {}          # pid -> record
        self.pver = 0               # bumped when a polity's lin, culture,
        self._ptab_key = None       # capital or end changes (ptab())
        self.next_pid = 1
        self.wars = {}              # (lo, hi) -> record
        self.truce = {}             # (lo, hi) -> tick until
        self.ties = {}              # (lo, hi) -> trade strength 0..1
        self.allies = {}            # (lo, hi) -> year formed
        self.ally_kind = {}         # (lo, hi) -> "affinity" | "balance"
        self.adj = set()
        self.cell_pol = -np.ones(N, int)
        self.cell_city = -np.ones(N, int)
        self.city_size = {}
        self.city_ts = []           # (year, id, cell, status, size, ...)
        self.ruins = {}             # cell -> record of the city that ended
        self.ts = []
        self.rel = []               # relations.csv rows (on frame ticks)
        self.hist = []              # history.npz snapshots (HIST_EVERY)
        self.war_log = []           # wars.csv (records only)
        self.siege_log = []         # sieges.csv
        self.revolt_log = []        # revolts.csv
        self._sim = {}
        self.start_sites()

    def new_state_v2(self):
        """State added 2026-11-09 (`food_flow`, urban population, deaths
        by cause). Also run by upgrade() on a state saved before then."""
        N = self.W.N
        self.ff_xo = np.zeros(N)          # rate the ruling people pay
        self.loc_in = np.zeros(N)         # food reaching a city's people
        self.city_c = -np.ones(N, int)    # people of each city cell
        self.ff_rec = {k: np.zeros(N) for k in ("rent", "prov", "cap",
                                                "trade")}
        self.fdist = {}                   # pid -> (capital, fver), dist
        self.cdist = np.full(N, np.inf)   # travel cost to the cell's city
        self.cb0 = np.ones(N)             # city-cell boost: base
        self.cboost = np.ones(N)          # and in full
        self.deaths = {}                  # cause -> deaths per people
        self.death_rows = []              # deaths.csv
        self.food_rows = []               # cityfood.csv

    def upgrade(self):
        """Bring a Sim pickled by older code up to this one (snapcheck)."""
        if not hasattr(self, "ff_on"):
            self.ff_on = self.dom_on and "food_flow" in self.on
            self.new_state_v2()
        if not hasattr(self, "uc_on"):
            self.uc_on = "urban_city" in self.on
        if not hasattr(self, "lver"):
            self.lver, self._ltab_ver, self._ltab_n = 0, -1, 0
        if not hasattr(self, "pver"):
            self.pver, self._ptab_key = 0, None
        if not hasattr(self.W, "Gf"):
            self.W.food_graph()

    def log(self, kind, text):
        self.events.append((self.year, kind, text))

    def pname(self, pid):
        p = self.polities.get(pid)
        return f"P{pid}({self.keys[p['culture']]})" if p else f"P{pid}"

    def lname(self, L):
        return f"L{L}({self.keys[self.Lpeople[L]]})"

    def place(self, i):
        return f"{self.W.lon[i]:+.1f},{self.W.lat[i]:+.1f}"

    def shock(self, cells, kind):
        """Note a blow to the cities among `cells`, for attributing their
        end later. Bookkeeping only."""
        for c in np.atleast_1d(cells):
            rec = self.cities.get(int(c))
            if rec is not None:
                sh = rec["shocks"]
                if not sh or sh[-1] != (self.year, kind):
                    sh.append((self.year, kind))
                    if len(sh) > 40:
                        del sh[:10]

    def end_cause(self, rec):
        """Why a city ended: the latest blow within SHOCK_WINDOW years,
        else the state of its land at the end."""
        recent = [k for y, k in rec["shocks"]
                  if self.year - y <= SHOCK_WINDOW]
        if recent:
            order = ["clearance", "sack", "raid takeover", "river lost",
                     "plague", "drought", "dragon", "raid", "siege"]
            return min(recent, key=lambda k: order.index(k)
                       if k in order else 99)
        c = rec["cell"]
        if self.salt[c] > 0.5:
            return "salted land"
        if self.land[c] < 0.6:
            return "worn land"
        if self.moist[c] < -1.0:
            return "dry climate"
        return "decline"

    def count(self, key, n=1):
        self.cnt[key] = self.cnt.get(key, 0) + n

    def first(self, key, kind, text):
        if key not in self.firsts:
            self.firsts.add(key)
            self.log(kind, text)

    def step(self):
        self._sim = {}
        self._pt = {}
        self.place_arrivals()
        self.technology()
        if self.ca_on:
            self.city_admin()
        self.prepare_capacity()
        self.famine()
        self.dragons()
        self.grow()
        self.migrate()
        self.raids()
        self.tidy()
        self.update_cities()
        self.territory()
        if self.year % ROAD_EVERY == 0:
            self.name_seats()
        if self.year % ROAD_EVERY == 0:
            self.roads()
        self.polity_stats()
        self.extraction()
        self.trade_posts()
        self.trade_ties()
        self.pref_spread()
        self.minorities()
        self.diplomacy()
        self.wars_step()
        self.rebellions()
        if self.rt:
            self.ruler_pull()
        if self.cc_on:
            self.city_culture()
            if self.year % PRICE_EVERY == 0:
                self.city_record()
        self.disasters()
        self.tidy()
        self.record()
        self.tick += 1
        self.year += DT

    def snapshot(self):
        """Map state for history.npz (figures.py's war and trade maps):
        people, population and state per cell, each live state's capital,
        people and size, and the trade ties. Reads state only."""
        st = [(pid, P["capital"], P["culture"], len(P["cities"]))
              for pid, P in self.polities.items()
              if P["ended"] is None and P.get("capital") is not None
              and P["capital"] >= 0]
        ti = [(a, b, t) for (a, b), t in self.ties.items() if t > 0 and
              self.live((a, b))]
        self.hist.append((self.year, self.cul.astype(np.int8),
                          self.pop.astype(np.float32),
                          self.cell_pol.astype(np.int32),
                          np.array(st, int).reshape(-1, 4),
                          np.array(ti, float).reshape(-1, 3)))

    def run(self, verbose=True):
        """Run to the end, writing output to self.out as it goes (frames
        when rendered, tables every FLUSH_EVERY ticks), so a killed run
        keeps what it had written."""
        from .output import Stream
        stream = Stream(self, self.out)
        t0 = time.time()
        nt = self.years // DT
        for _ in range(nt):
            self.step()
            if self.tick % self.frame_every == 0 or self.tick == nt:
                stream.frame(render(self))
                self.relations()
            if self.tick % HIST_EVERY == 0 or self.tick == nt:
                self.snapshot()
            if self.tick % FLUSH_EVERY == 0 or self.tick == nt:
                stream.flush()
            if verbose and self.tick % 50 == 0:
                s = self.ts[-1]
                tot = sum(s[f"pop_{k}"] for k in self.keys)
                nlin = sum(s[f"lineages_{k}"] for k in self.keys)
                print(f"yr {self.year:5d}  pop {tot/1e6:7.2f}M  cities "
                      f"{len(self.cities):4d}  states {s['n_polities']:4d}"
                      f"  lineages {nlin:4d}  allies {len(self.allies):3d}"
                      f"  wars {len(self.wars):3d}  "
                      f"[{time.time()-t0:5.0f}s]", flush=True)


# ---- rendering -----------------------------------------------------------
