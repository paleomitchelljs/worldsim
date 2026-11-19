"""The simulation: state and the yearly step."""
import os
import pickle
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
from .shared import SharedMixin
from .render import *  # noqa: F401,F403


class Sim(CitiesMixin, LandMixin, EconomyMixin, SettlementMixin, DragonsMixin, CultureMixin, StatesMixin, WarMixin, TechnologyMixin, DiagnosticsMixin, SharedMixin):
    def __init__(self, world, seed=1, years=6000, frame_every=10, out=None,
                 homelands="continents", peoples=None, start_pool=0.0,
                 starts=3, start_vary=0.05, drift=0.06, cluster_km=0.0,
                 settle_drift=0.03, size_food="kleiber", start_mode="wander",
                 wander_steps=2000, off=(), shuffle_sites=False,
                 sites="sites.json", on=()):
        self.W = W = world
        self.on = (set(FEATURES) - set(off)) | set(on)
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
        self.seed = seed
        # every draw comes from a named stream (R); rseed seeds them, and
        # a branch may set a fresh one (reseed)
        self.rseed, self.rngs = seed, {}
        self.years = years
        self.frame_every = frame_every
        self.hist_every = HIST_EVERY
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
        nK = len(TRAITS) + len(XTRAITS)
        self.CE = np.full((CITY_MAX, nK), 0.5)   # city elites
        self.CM = np.full((CITY_MAX, nK), 0.5)   # city commons
        self.Chome = -np.ones(CITY_MAX, int)     # plurality lineage
        self.flags()
        self._pt = {}
        self.Cmem = np.zeros((CITY_MAX, 5))       # war, trade, hard, raid, revolt
        self.CH = np.zeros((CITY_MAX, nK))        # commons' own history
        self.Ctnear = np.zeros(CITY_MAX)          # local trade reach
        self.Cwcap = np.zeros(CITY_MAX)           # capital's share of influence
        self.Cwown = np.zeros(CITY_MAX)           # own state's share
        self.city_rows, self.city_gap_rows, self.city_trait_rows = [], [], []
        self.Cadm = np.zeros(CITY_MAX)            # city administration
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
                            # sea factor, distances, cells reached]
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
        self.rows_new(N)                  # the presence table (WP7 B)
        self.rows_pending = []            # rows queued for it (WP7 C)
        self.sh_on = "shared_cells" in self.on
        self.dp_on = "displacement" in self.on
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
        self.rul_c = -np.ones(N, int)     # ruling people of the cell's state
        self.rul_est = np.zeros(N)        # its state's establishment
        self.ext_x = np.zeros(N)          # extraction rate on subjects
        self.ext_in = np.zeros(N)         # food received (ruling people)
        self.new_state_v2()
        self.imm = np.zeros(N)            # plague immunity
        self.epi = []                     # epidemics under way (WP6 C)
        self.pmem = np.zeros(N)           # people, mean of ~50 yr (upkeep)
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
        # the climate's stream ("climate") is its own, like every other:
        # the same seed gives the same climate whatever else is on
        self.climate_setup()
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
        self.truce = {}             # (lo, hi) -> year until
        self.clock_years = True     # truces, wars, plague gap in years
        self.dtp = DT               # years in the political (sub-)step
        self.army_x = np.zeros(self.W.N)  # capacity share armies eat
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
        self.new_state_v3()

    def new_state_v3(self):
        """State added in WP4 stage A (food ledger). Also run by upgrade()
        on an older state."""
        self.fl_rows = []                 # food.csv
        self.fl_new()
        self.tr_x = np.zeros(self.W.N)    # `trade_debit`: rate sold
        self.new_state_v4()

    def new_state_v4(self):
        """State added in WP4 stage C (growth account). Also run by
        upgrade() on an older state; its first century starts at the
        first mark after loading."""
        self.growth_rows = []             # growth.csv
        self.ac_dead = np.zeros(self.nP)  # removals recorded, cumulative
        self.ac_made = np.zeros(self.nP)  # heads added from no cell
        self.ac_last = self.ac_dlast = self.ac_mlast = None
        self.ac_new()
        self.new_state_v5()

    def new_state_v5(self):
        """State added 2026-11-18 (U): each site's own defence
        (`site_defence`), a fixed draw per cell so that a city refounded
        on the same site keeps it. exp(SITE_DEF_SD x t(SITE_DEF_DF)),
        clipped to SITE_DEF_LIM: most sites near 1, a few weak, a few
        very hard. Drawn on its own stream, so no other draw moves."""
        t = self.R("site_defence").standard_t(SITE_DEF_DF, self.W.N)
        self.site_def = np.clip(np.exp(SITE_DEF_SD * t), *SITE_DEF_LIM)

    def city_def(self, c):
        """Terrain defence of a city at cell c, times its site's own
        (`site_defence`)."""
        d = self.W.defence[c]
        return d * self.site_def[c] if "site_defence" in self.on else d

    def R(self, name):
        """The run's random stream `name` (geo.stream), made when first
        asked for."""
        g = self.rngs.get(name)
        if g is None:
            g = self.rngs[name] = stream(self.rseed, name)
        return g

    def reseed(self, seed):
        """Start every stream afresh from `seed` (a branch's own seed).
        What was drawn at setup (climate series, abrupt events, sites,
        founders) stays as saved."""
        self.rseed, self.rngs = seed, {}

    def flags(self):
        """The shorthand flags for switches in self.on (set again when a
        branched run switches mechanics off)."""
        self.cc_on = "city_culture" in self.on
        self.dom_on = "dominion" in self.on
        # `food_flow` works through dominion's extraction
        self.ff_on = self.dom_on and "food_flow" in self.on
        self.td_on = self.ff_on and "trade_debit" in self.on
        self.uc_on = "urban_city" in self.on
        self.ca_on = self.cc_on and "city_admin" in self.on
        self.rt = "ruler_traits" in self.on and "rulers" in self.on

    # per-cell views of the presence table's first two rows
    ROW_VIEWS = ("pop", "cul", "lin", "mpop", "mcul", "mlin", "mcap")

    def rows_new(self, N):
        """The presence table (WP7 B): one row per people present in a
        cell, with its cell (`rc`), people (`rp`), lineage (`rl`), heads
        (`rh`) and, for a merchant quarter, a cap flag (`rm`). Row i < N
        is cell i's main people and row N + i its minority, so `pop`,
        `cul`, `lin` and `mpop`, `mcul`, `mlin`, `mcap` are views of those
        rows and every routine reads and writes the table through them. An
        empty row has people -1."""
        self.rc = np.tile(np.arange(N), 2)
        self.rp = -np.ones(2 * N, int)
        self.rl = -np.ones(2 * N, int)
        self.rh = np.zeros(2 * N)
        self.rm = np.zeros(2 * N, bool)
        self.rows_bind()

    def rows_bind(self):
        """Point the per-cell views at the table (after it is built,
        loaded or reallocated)."""
        N = self.W.N
        self.pop, self.mpop = self.rh[:N], self.rh[N:2 * N]
        self.cul, self.mcul = self.rp[:N], self.rp[N:2 * N]
        self.lin, self.mlin = self.rl[:N], self.rl[N:2 * N]
        self.mcap = self.rm[N:2 * N]

    def __getstate__(self):
        # a pickled view would come back as a copy cut off from the
        # table: leave the views out and rebind them on loading
        d = self.__dict__.copy()
        if "rh" in d:
            for k in self.ROW_VIEWS:
                d.pop(k, None)
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        if "rh" in d:
            self.rows_bind()

    def save(self, path):
        """Pickle the whole Sim, a state to branch from (worldsim.py
        --save-state). The travel and food distance caches are left out:
        they are rebuilt, to the same values, when next asked. The run's
        run.json as of the save goes in with it (state_info), so a branch
        can record what it grew from.

        Unpickling rebuilds sets, whose iteration order can then differ
        from the originals', so a loaded state would not continue exactly
        as the run that saved it. The run therefore carries on from the
        saved copy itself: it and every branch from the file continue
        alike (a run that saves can differ, after the save year, from one
        that does not)."""
        from .output import run_info
        self.state_info = run_info(self)
        self.pdist, self.fdist = {}, {}
        b = pickle.dumps(self, protocol=5)
        with open(path + ".tmp", "wb") as fh:
            fh.write(b)
        os.replace(path + ".tmp", path)
        new = pickle.loads(b)
        del b
        self.__dict__.clear()
        self.__dict__.update(new.__dict__)

    def upgrade(self):
        """Bring a Sim pickled by older code up to this one (snapcheck)."""
        if not hasattr(self, "ff_on"):
            self.ff_on = self.dom_on and "food_flow" in self.on
            self.new_state_v2()
        if not hasattr(self, "fl_rows"):
            self.new_state_v3()
        if not hasattr(self, "growth_rows"):
            self.new_state_v4()
        if not hasattr(self, "site_def"):
            self.new_state_v5()
        if not hasattr(self, "td_on"):
            self.td_on = False
        if not hasattr(self, "uc_on"):
            self.uc_on = "urban_city" in self.on
        if not hasattr(self, "lver"):
            self.lver, self._ltab_ver, self._ltab_n = 0, -1, 0
        if self.events and not isinstance(self.events[0], dict):
            # before WP2 stage A: (year, kind, text)
            self.events = [dict(year=y, kind=k, text=t)
                           for y, k, t in self.events]
        if not hasattr(self, "rngs"):
            # before WP1 stage F: one shared stream and a few offsets;
            # such a state continues on fresh named streams
            self.rseed, self.rngs = self.seed, {}
        if not hasattr(self, "hist_every"):
            # before WP3 stage A: snapshots every 20 ticks, as tuples
            # (year, people, pop, polity, states, ties)
            self.hist_every = 20
            N = self.W.N
            self.hist = [dict(
                year=h[0], people=h[1], lineage=np.full(N, -1, np.int32),
                polity=h[3], minority=np.full(N, -1, np.int8),
                pop_log1p=np.log1p(h[2]).astype(np.float16),
                herding=np.zeros(N, bool), st=h[4], tie=h[5],
                city=np.zeros((0, 5))) for h in self.hist]
        if not hasattr(self, "pver"):
            self.pver, self._ptab_key = 0, None
        if not hasattr(self.W, "Gf"):
            self.W.food_graph()
        if not hasattr(self, "dtp"):
            self.dtp = DT
        if not hasattr(self, "rh"):
            # before WP7 B: separate per-cell arrays for the main people
            # and the minority; copy them into the presence table
            old = [getattr(self, k) for k in self.ROW_VIEWS]
            self.rows_new(self.W.N)
            for k, v in zip(self.ROW_VIEWS, old):
                getattr(self, k)[:] = v
        if not hasattr(self, "rows_pending"):
            self.rows_pending = []
            self.sh_on = "shared_cells" in self.on
            self.dp_on = "displacement" in self.on
        if not hasattr(self, "epi"):
            self.epi = []
        if not hasattr(self, "pmem"):
            self.pmem = self.pop.copy()
        if not hasattr(self, "army_x"):
            self.army_x = np.zeros(self.W.N)
        if hasattr(self, "fl_acc") and len(self.fl_acc["world"]) != \
                len(self.FL_CELL) + len(self.FL_STATE):
            # a ledger line was added (WP5 E, taken_army): the century
            # under way starts afresh (records only)
            self.fl_new()
        if not hasattr(self, "clock_years"):
            # before WP5 stage C: truces, war starts and last sieges, and
            # the plague gap were held in ticks
            self.clock_years = True
            self.truce = {k: v * DT for k, v in self.truce.items()}
            for w in self.wars.values():
                for a in ("start", "last_siege"):
                    if a in w:
                        w[a] *= DT
            if hasattr(self, "_plague_next"):
                self._plague_next *= DT

    def log(self, kind, text, **data):
        """Record an event (WP2 stage A): year, kind, text and whatever
        of these the call site has in hand: cell (the place), polities
        (ids, the actor first), peoples (keys), lineages, cities (ids), n
        (a magnitude: people dead, cities taken, years). Written to
        events.txt and events.jsonl (output.Stream)."""
        e = dict(year=self.year, kind=kind, text=text)
        for k, v in data.items():
            if v is not None:
                e[k] = plain(v)
        self.events.append(e)

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
                     "plague", "drought", "dragon", "raid", "ravage",
                     "siege"]
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

    def first(self, key, kind, text, **data):
        """Log an event only the first time `key` is seen."""
        if key not in self.firsts:
            self.firsts.add(key)
            self.log(kind, text, **data)

    def politics(self):
        """Diplomacy, war and rebellion. Under `pol_step` they run DT /
        DT_POL times a tick, each over self.dtp years, on the polity
        statistics of the tick; after a sub-step in which a city changed
        hands, territory and strength are refreshed (pol_refresh)."""
        n = max(1, round(DT / DT_POL)) if "pol_step" in self.on else 1
        self.dtp = DT / n
        y0 = self.year
        for i in range(n):
            y = y0 + i * self.dtp
            self.year = int(y) if float(y).is_integer() else y
            held = [c["polity"] for c in self.cities.values()]
            self.diplomacy()
            self.acct_mark("diplomacy")
            self.wars_step()
            self.acct_mark("wars")
            self.rebellions()
            self.acct_mark("rebellions")
            if "camps" in self.on:
                self.decamp()
            if i < n - 1 and held != [c["polity"]
                                      for c in self.cities.values()]:
                self.pol_refresh()
        self.year = y0
        self.dtp = DT

    def step(self):
        self._sim = {}
        self._pt = {}
        self.place_arrivals()
        self.technology()
        if self.ca_on:
            self.city_admin()
        self.prepare_capacity()
        self.acct_mark("arrivals")
        self.famine()
        self.acct_mark("famine")
        self.dragons()
        self.acct_mark("dragons")
        self.grow()
        self.acct_mark("grow")
        self.migrate()
        if self.sh_on:
            self.infiltrate()
        self.acct_mark("migrate")
        self.raids()
        if self.sh_on:
            self.inner_raids()
        self.acct_mark("raids")
        self.tidy()
        self.update_cities()
        self.camps_step()
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
        self.acct_mark("states")
        self.minorities()
        self.acct_mark("minorities")
        self.politics()
        if self.rt:
            self.ruler_pull()
        if self.cc_on:
            self.city_culture()
            if self.year % PRICE_EVERY == 0:
                self.city_record()
        self.acct_mark("culture")
        self.disasters()
        self.acct_mark("disasters")
        self.tidy()
        self.acct_mark("tidy")
        self.record()
        self.tick += 1
        self.year += DT

    def snapshot(self):
        """Map state for history.npz, enough for a renderer to need
        nothing else (WP3 stage A): per cell, people, lineage, state,
        minority people, population (float16 of log1p; under 0.5% off
        after expm1) and the herding flag; each live state's capital,
        people and cities; the trade ties; each city's cell, id, size
        (urban, food-equivalents), state and capital flag. Reads state
        only."""
        st = [(pid, P["capital"], P["culture"], len(P["cities"]))
              for pid, P in self.polities.items()
              if P["ended"] is None and P.get("capital") is not None
              and P["capital"] >= 0]
        ti = [(a, b, t) for (a, b), t in self.ties.items() if t > 0 and
              self.live((a, b))]
        caps = {P["capital"] for P in self.polities.values()
                if P["ended"] is None}
        ct = [(c, r["id"], self.city_size.get(c, 0.0), r["polity"],
               c in caps) for c, r in self.cities.items()]
        self.hist.append(dict(
            year=self.year, people=self.cul.astype(np.int8),
            lineage=self.lin.astype(np.int32),
            polity=self.cell_pol.astype(np.int32),
            minority=self.mcul.astype(np.int8),
            pop_log1p=np.log1p(np.maximum(self.pop, 0)).astype(np.float16),
            herding=self.herding.copy(),
            st=np.array(st, int).reshape(-1, 4),
            tie=np.array(ti, float).reshape(-1, 3),
            city=np.array(ct, float).reshape(-1, 5)))

    def run(self, verbose=True, saves=None):
        """Run from the current tick to the end (a loaded state continues
        where it was saved), writing output to self.out as it goes (frames
        when rendered, tables every FLUSH_EVERY ticks), so a killed run
        keeps what it had written. saves: {year: path}, a saved state
        after the tick that reaches each year."""
        from .output import Stream
        stream = Stream(self, self.out)
        t0 = time.time()
        nt = self.years // DT
        todo = sorted((saves or {}).items())
        while self.tick < nt:
            self.step()
            while todo and self.year >= todo[0][0]:
                self.save(todo[0][1])
                if verbose:
                    print(f"saved state at year {self.year} -> "
                          f"{todo[0][1]}", flush=True)
                todo.pop(0)
            if self.tick % self.frame_every == 0 or self.tick == nt:
                stream.frame(render(self))
                self.relations()
            if self.tick % self.hist_every == 0 or self.tick == nt:
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


def plain(v):
    """v with numpy scalars and arrays made into Python numbers and lists
    (for JSON)."""
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, (list, tuple, set)):
        return [plain(x) for x in v]
    return v


# ---- rendering -----------------------------------------------------------
