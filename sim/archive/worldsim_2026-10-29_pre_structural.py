"""
Zero-player civilization simulator on world.gpkg.

Full documentation: sim/docs/README.md (rules, traits, startup, data).

Peoples (a roster module, --peoples) start as founding bands and grow,
migrate, farm, found cities, form polities, trade, raid, conquer, clear
land, rebel, and collapse on the 0.5-degree world grid. Nobody plays it;
you watch what the map does.

Three layers, each driving the next:

  people     population, people and lineage per land cell. Peoples never
             mix: a cell holds one people or none. Each people starts as
             several founding groups; each group is a lineage with its own
             slightly different traits and its own technology. Lineages
             split (secession, colonies on new land) with small mutations,
             learn technology from lineages they touch, and are absorbed
             into the ruling lineage of their own people over time. A people can move into
             empty land, or into land another people has lost (raided out,
             cleared by conquest, emptied by famine or plague).
  cities     a cell becomes a city when it is dense and locally central
             (river, coast, ore, trade). Each city rules the land nearest
             to it by travel cost, out to its people's administrative reach.
  polities   a set of cities under one capital, ruled by a lineage.
             Tolerant neighbours trade, ally and may fuse into one state,
             the threshold rising with how unlike they are (kin easily,
             other peoples only if both are highly tolerant). Polities make
             war on
             neighbours (land or, for sailors, sea), take cities, absorb or
             clear conquered foreigners, trade with partners, and fragment
             when cohesion (asabiya) runs down and provinces lie far from
             the capital.

One tick is DT years. The world file is opened read-only.

Run:  ~/.venvs/worldsim/bin/python worldsim.py --seed 1 --years 4000
Out:  sim/runs/seed<N>/  (history.gif, final.png, legacy.png,
      population.png, events.txt, cities.csv, polities.csv, timeseries.csv)
"""
import argparse
import importlib
import csv
import json
import math
import os
import sqlite3
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from peoples import PEOPLES  # noqa: E402

GPKG = os.path.join(HERE, "..", "gis", "world.gpkg")
NY, NX = 360, 720
R_EARTH = 6371.0
BIOMES = ["Jungle", "Desert", "Grassland", "Temperate forest", "Tundra"]

# ---- assumptions ---------------------------------------------------------
DT = 5                      # years per tick
# Forager density (people/km2) by biome.
FORAGE = {"Jungle": 0.25, "Temperate forest": 0.18, "Grassland": 0.15,
          "Desert": 0.02, "Tundra": 0.03}
# Rain-fed farming suitability by biome (multiplies soil fertility).
FARM = {"Jungle": 0.45, "Temperate forest": 0.75, "Grassland": 1.0,
        "Desert": 0.04, "Tundra": 0.03}
# Floodplain irrigation response by biome: dry climates gain the most.
IRRIG = {"Jungle": 0.4, "Temperate forest": 0.6, "Grassland": 0.9,
         "Desert": 1.0, "Tundra": 0.05}
FARM_MAX_DENS = 1.8         # people/km2 on the best rain-fed soil
IRRIG_MAX_DENS = 9.0        # people/km2 added on a big floodplain
# Travel cost multiplier by biome (cost-km per km).
MOVE = {"Jungle": 1.7, "Temperate forest": 1.25, "Grassland": 1.0,
        "Desert": 1.5, "Tundra": 1.8}
STRAIT_KM = 160.0           # coastal cells this close link across water
# Biome preference: habitability = best * (affinity / best) ** k. k starts at
# BIOME_K and falls toward BIOME_K * (1 - BIOME_ADAPT) = 1 (the roster's own
# numbers) as farming and metallurgy let a lineage live off its home biome.
BIOME_K = 2.5
BIOME_ADAPT = 0.6
# Sea dispersal: voyage targets are weighted by exp(-d / D),
# D = SAIL_D0 + SAIL_D1 * sail ** 1.5 (km). No minimum range.
SAIL_D0, SAIL_D1 = 40.0, 2500.0
# Military multiplier from metal: 1 + bronze + iron + 1.5 * steel
METAL_MIL = (1.0, 1.0, 1.5)
# Farm yield from tools: 1 + iron + steel terms
TOOLS = (0.25, 0.25)
# Terrain. Defence: a siege defender's strength is multiplied by
# TERRAIN_DEF[biome] * (1 + DEF_RELIEF * relief_km[<=1.5]) * (1 + DEF_WET * wet)
TERRAIN_DEF = {"Grassland": 1.0, "Temperate forest": 1.1, "Tundra": 1.3,
               "Desert": 1.6, "Jungle": 1.7}
DEF_RELIEF, DEF_WET = 0.6, 0.6
# Colonization: settling a cell is weighted by
# exp(-relief_km / COL_RELIEF) * (1 - COL_WET * wet)
COL_RELIEF, COL_WET = 0.7, 0.5
# Rivers. Dispersal: a pioneer leaving a river cell follows the river (up or
# downstream) with probability RIV_LEAP, up to RIV_STEPS[0] + RIV_STEPS[1] *
# sail cells; budding from a river cell to a river cell is favoured by
# (1 + RIV_BUD). Trade: tie growth x (1 + RIV_TRADE * mean share of the two
# states' cities on rivers) x (1 + BASIN_TRADE if they share a river basin).
RIV_LEAP, RIV_STEPS, RIV_BUD = 0.6, (6, 30), 1.0
RIV_TRADE, BASIN_TRADE = 1.0, 0.5
FOUND_MIN = 10.0            # smallest band that can claim an empty cell
CITY_POP = 6000.0           # food-equivalent cell population for a city
CITY_KEEP = 0.35            # a city is abandoned below this x its threshold
# City size cap (food-equivalent people in the city cell), set by the ruling
# lineage's administration: CITY_POP * (CITY_CAP0 + CITY_CAP1 * admin**2).
CITY_CAP0, CITY_CAP1 = 3.0, 40.0
REACH0, REACH1 = 120.0, 900.0   # admin reach (cost-km) = REACH0 + REACH1*admin


def unit_xyz(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo),
                     np.sin(la)], -1)


def gc_km(xyz, i, j):
    """Great-circle km between cell i and cells j."""
    ch = np.linalg.norm(xyz[j] - xyz[i], axis=-1)
    return 2 * R_EARTH * np.arcsin(np.clip(ch / 2, 0, 1))


TRAITS = ["violence", "expansion", "separation", "cohesion", "statecraft",
          "innovation", "seafaring", "trade", "tolerance"]
TI = {t: k for k, t in enumerate(TRAITS)}
TRAIT_ATTR = dict(violence="viol", expansion="expn", separation="sep",
                  cohesion="coh", statecraft="state", innovation="innov",
                  seafaring="seaf", trade="trade", tolerance="tol")
MAXL = 60000                # lineage table size
BLOCK = 10                  # settlement regions are BLOCK x BLOCK cells (5 deg)
# Similarity between two lineages: within a people exp(-d/SIM_SAME_SCALE)
# of their trait distance d; between peoples a + b*exp(-d/0.8), capped low.
SIM_SAME_SCALE = 0.8
SIM_OTHER = (0.15, 0.35)
# (share of dissimilarity each side's tolerance must cover, softness)
TOL_TRADE = (0.4, 0.15)
TOL_ALLY = (0.8, 0.08)
TOL_FUSE = (1.0, 0.06)


def vary_peoples(peoples, seed, amount):
    """Jitter every people's cultural traits for one run, on the logit
    scale by N(0, amount), so archetypes bend without all collapsing to the
    middle. Intrinsic traits (r, biome affinity, size) are left as given."""
    if amount <= 0:
        return [dict(p) for p in peoples]
    rng = np.random.default_rng(10_000 + seed)
    out = []
    for p in peoples:
        q = dict(p)
        for t in TRAITS:
            x = np.clip(p.get(t, 0.5), 0.02, 0.98)
            z = math.log(x / (1 - x)) + rng.normal(0, 2.5 * amount)
            q[t] = round(float(1 / (1 + math.exp(-z))), 2)
        out.append(q)
    return out


# ---- world ---------------------------------------------------------------
class World:
    def __init__(self, gpkg=GPKG):
        con = sqlite3.connect(f"file:{os.path.abspath(gpkg)}?mode=ro",
                              uri=True)
        cols = ["row", "col", "lon", "lat", "area_km2", "fic_land",
                "fic_elev_km", "fic_biome", "fic_soil_bar_value",
                "syn_relief_km", "syn_discharge_m3s", "syn_river",
                "syn_lake", "syn_reach_productivity", "syn_dist_copper_km",
                "syn_dist_tin_km", "syn_dist_iron_km", "syn_surface_lith",
                "syn_alluvial_fill", "syn_runoff_m_yr", "fid",
                "syn_flow_to", "syn_basin_id", "syn_wetness"]
        rows = con.execute(f"select {','.join(cols)} from cells").fetchall()
        con.close()
        d = {c: [r[k] for r in rows] for k, c in enumerate(cols)}

        def num(c, fill=0.0):
            a = np.array([fill if v is None else v for v in d[c]], float)
            return np.where(np.isfinite(a), a, fill)

        row = num("row").astype(int)
        col = num("col").astype(int)
        land2 = np.zeros((NY, NX), bool)
        land2[row, col] = num("fic_land") > 0
        prod2 = np.zeros((NY, NX))
        prod2[row, col] = num("syn_reach_productivity")
        self.land2 = land2

        L = num("fic_land") > 0
        self.row, self.col = row[L], col[L]
        self.lon, self.lat = num("lon")[L], num("lat")[L]
        self.area = num("area_km2")[L]
        self.elev = num("fic_elev_km")[L]
        self.relief = num("syn_relief_km")[L]
        # swamp layer (derive_world.swamp_wetness): 0-1
        self.wet = num("syn_wetness")[L]
        self.Q = num("syn_discharge_m3s")[L]
        self.river = num("syn_river")[L] > 0
        # river network: downstream land cell (or -1) and upstream river
        # cells, for travel along rivers; basin ids for river trade
        fid = num("fid").astype(np.int64)
        fl = num("syn_flow_to", -1).astype(np.int64)
        lidx = {int(f) - 1: k for k, f in enumerate(fid[L])}  # flow_to is
        # a 0-based cell index (fid - 1)
        down = np.array([lidx.get(int(t), -1) for t in fl[L]])
        self.down = np.where(self.river, down, -1)
        self.down[self.down >= 0] = np.where(
            self.river[self.down[self.down >= 0]], self.down[self.down >= 0],
            -1)
        self.up = [[] for _ in range(int(L.sum()))]
        for k in np.nonzero(self.down >= 0)[0]:
            self.up[self.down[k]].append(int(k))
        self.basin = num("syn_basin_id", -1).astype(np.int64)[L]
        self.lake = num("syn_lake")[L] > 0
        self.d_cu = num("syn_dist_copper_km", 9e9)[L]
        self.d_sn = num("syn_dist_tin_km", 9e9)[L]
        self.d_fe = num("syn_dist_iron_km", 9e9)[L]
        soil = num("fic_soil_bar_value", np.nan)[L]
        biome = np.array(d["fic_biome"], object)[L]
        lith = np.array(d["syn_surface_lith"], object)[L]
        self.biome = np.array([BIOMES.index(b) if b in BIOMES else 4
                               for b in biome])
        self.N = N = L.sum()
        self.xyz = unit_xyz(self.lon, self.lat)

        idx = -np.ones((NY, NX), int)
        idx[self.row, self.col] = np.arange(N)
        self.idx2 = idx
        offs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1),
                (1, 0), (1, 1)]
        nb = -np.ones((N, 8), int)
        nd = np.zeros((N, 8))
        coastal = np.zeros(N, bool)
        coast_prod = np.zeros(N)
        for k, (dr, dc) in enumerate(offs):
            r2 = self.row + dr
            c2 = (self.col + dc) % NX
            ok = (r2 >= 0) & (r2 < NY)
            r2c = np.clip(r2, 0, NY - 1)
            nb[:, k] = np.where(ok, idx[r2c, c2], -1)
            sea = ok & ~land2[r2c, c2]
            coastal |= sea
            coast_prod = np.maximum(coast_prod,
                                    np.where(sea, prod2[r2c, c2], 0))
            dy = 0.5 * 111.2 * dr
            dx = 0.5 * 111.2 * np.cos(np.radians(self.lat)) * dc
            nd[:, k] = np.maximum(np.hypot(dx, dy), 1.0)
        self.nb, self.coastal = nb, coastal

        # travel cost per cell, then per edge
        tc = (1 + 1.5 * np.clip(self.relief, 0, 2)) * \
            np.array([MOVE[b] for b in BIOMES])[self.biome]
        tc = np.where(self.river, 0.7 * tc, tc)
        ec = np.zeros((N, 8))
        for k in range(8):
            j = nb[:, k]
            ec[:, k] = np.where(j >= 0, nd[:, k] * 0.5 *
                                (tc + tc[np.maximum(j, 0)]), np.inf)
        self.edgecost = ec
        self.defence = np.array([TERRAIN_DEF[b] for b in BIOMES])[self.biome] \
            * (1 + DEF_RELIEF * np.clip(self.relief, 0, 1.5)) * \
            (1 + DEF_WET * self.wet)
        self.colonize = np.exp(-np.clip(self.relief, 0, None) / COL_RELIEF) \
            * (1 - COL_WET * self.wet)

        # undirected edge list (each land pair once)
        e1, e2, ew = [], [], []
        for k in (2, 4, 6, 7):          # NE, E, S, SE
            j = nb[:, k]
            m = j >= 0
            e1.append(np.nonzero(m)[0]); e2.append(j[m]); ew.append(ec[m, k])
        self.E1, self.E2 = np.concatenate(e1), np.concatenate(e2)
        EW = np.concatenate(ew)

        # short sea crossings between coastal cells
        ci = np.nonzero(coastal)[0]
        self.coast_idx = ci
        self.coast_tree = cKDTree(self.xyz[ci])
        pairs = np.array(sorted(self.coast_tree.query_pairs(
            2 * math.sin(STRAIT_KM / R_EARTH / 2))), int)
        if len(pairs):
            a, b = ci[pairs[:, 0]], ci[pairs[:, 1]]
            dkm = 2 * R_EARTH * np.arcsin(np.clip(np.linalg.norm(
                self.xyz[a] - self.xyz[b], axis=1) / 2, 0, 1))
            far = dkm > 90          # not already a land neighbour
            sa, sb, sw = a[far], b[far], 2.0 * dkm[far]
        else:
            sa = sb = sw = np.array([], int)
        I = np.concatenate([self.E1, self.E2, sa, sb])
        J = np.concatenate([self.E2, self.E1, sb, sa])
        Wt = np.concatenate([EW, EW, sw, sw])
        self.G = sparse.csr_matrix((Wt, (I, J)), shape=(N, N))

        # landmasses (for logging first landings)
        lab, nlab = ndimage.label(land2, structure=np.ones((3, 3)))
        self.landmass = lab[self.row, self.col]
        self.landmass_area = np.bincount(self.landmass, weights=self.area)

        # ---- carrying capacity (people/km2) before people-specific terms
        fert = np.where(np.isfinite(soil), np.clip((soil + 3.75) / 5.5,
                                                   0, 1), 0.3)
        b = self.biome
        pn = np.clip((coast_prod - 0.0003) / 0.0006, 0, 1)
        near_river = self.river | (self.Q > 50)
        forage = np.array([FORAGE[x] for x in BIOMES])[b] * \
            (1 + 2.0 * coastal * pn) * (1 + 0.8 * near_river)
        elevpen = np.clip(1 - (self.elev - 1.5) / 1.5, 0.2, 1) / \
            (1 + 0.5 * np.clip(self.relief, 0, 2))
        farm = FARM_MAX_DENS * fert ** 1.3 * \
            np.array([FARM[x] for x in BIOMES])[b] * elevpen
        irr = IRRIG_MAX_DENS * np.sqrt(np.clip(self.Q / 3000, 0, 1)) * \
            np.array([IRRIG[x] for x in BIOMES])[b] * self.river
        alluv = np.array([l == "alluvium" for l in lith])
        farm = (farm + irr) * np.where(alluv, 1.3, 1.0) * \
            np.where(self.lake, 1.2, 1.0) + 1.0 * coastal * pn
        self.forage, self.farm = forage, farm
        self.locus = (1 + 0.6 * self.river + 0.4 * coastal +
                      0.3 * (np.minimum(self.d_cu, self.d_sn) < 150) +
                      0.2 * (self.d_fe < 100))

        # rendering base
        base = np.zeros((NY, NX, 3), np.uint8)
        base[:] = (28, 48, 78)
        bcol = np.array([(62, 96, 58), (176, 160, 118), (128, 138, 84),
                         (84, 112, 72), (176, 182, 184)], np.uint8)
        base[self.row, self.col] = bcol[b]
        shade = np.clip(1 - 0.25 * np.clip(self.relief, 0, 1.5), 0.6, 1)
        base[self.row, self.col] = (base[self.row, self.col] *
                                    shade[:, None]).astype(np.uint8)
        self.base = base
        rows_land = np.nonzero(land2.sum(1) > 40)[0]
        self.r0 = max(0, rows_land.min() - 8)
        self.r1 = min(NY, rows_land.max() + 4)


# ---- simulation ----------------------------------------------------------
def sigmoid(x):
    return 1 / (1 + math.exp(-max(-50.0, min(50.0, x))))


class Sim:
    def __init__(self, world, seed=1, years=6000, frame_every=10, out=None,
                 homelands="continents", peoples=None, start_pool=0.0,
                 starts=3, start_vary=0.05, drift=0.06, cluster_km=0.0,
                 settle_drift=0.03, size_food="kleiber", start_mode="wander",
                 wander_steps=2000):
        self.W = W = world
        self.homelands = homelands
        self.start_pool = start_pool
        self.starts = starts
        self.start_vary = start_vary
        self.drift = drift
        self.cluster_km = cluster_km
        self.settle_drift = settle_drift
        self.start_mode = start_mode
        self.wander_steps = wander_steps
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
        self.Lpeople = -np.ones(MAXL, int)
        self.Lparent = -np.ones(MAXL, int)
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
        self.admin = np.zeros(MAXL)
        self.bronze = np.zeros(MAXL, bool)
        self.iron = np.zeros(MAXL, bool)
        self.steel = np.zeros(MAXL, bool)
        self.nL = 0
        for t, k in TI.items():           # column views, kept in sync
            setattr(self, TRAIT_ATTR[t], self.LT[:, k])

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
        self.next_pid = 1
        self.wars = {}              # (lo, hi) -> record
        self.truce = {}             # (lo, hi) -> tick until
        self.ties = {}              # (lo, hi) -> trade strength 0..1
        self.allies = {}            # (lo, hi) -> year formed
        self.adj = set()
        self.cell_pol = -np.ones(N, int)
        self.cell_city = -np.ones(N, int)
        self.city_size = {}
        self.ts = []
        self.frames = []
        self._sim = {}
        self.start_sites()

    # ---- helpers
    def log(self, kind, text):
        self.events.append((self.year, kind, text))

    def pname(self, pid):
        p = self.polities.get(pid)
        return f"P{pid}({self.keys[p['culture']]})" if p else f"P{pid}"

    def lname(self, L):
        return f"L{L}({self.keys[self.Lpeople[L]]})"

    def place(self, i):
        return f"{self.W.lon[i]:+.1f},{self.W.lat[i]:+.1f}"

    def first(self, key, kind, text):
        if key not in self.firsts:
            self.firsts.add(key)
            self.log(kind, text)

    # ---- lineages
    def new_lineage(self, people, parent, how, sd=0.0):
        """A new lineage: a founding group of a people, or a daughter of an
        existing lineage (secession, settlers, colony). Intrinsic traits
        (growth rate, biome affinity) and technology pass on unchanged;
        cultural traits mutate by `sd` on the logit scale."""
        if self.nL >= MAXL:
            return parent if parent >= 0 else 0
        L = self.nL
        self.nL += 1
        rng = self.rng
        if parent >= 0:
            T, r, aff = self.LT[parent], self.Lr[parent], self.Laff[parent]
            for a in ("agri", "metal", "sail", "admin", "bronze", "iron",
                      "steel"):
                getattr(self, a)[L] = getattr(self, a)[parent]
        else:
            T, r, aff = self.pT[people], self.pr[people], self.paff[people]
            self.agri[L] = 0.25
        if sd > 0:
            x = np.clip(T, 0.02, 0.98)
            T = 1 / (1 + np.exp(-(np.log(x / (1 - x)) +
                                  rng.normal(0, 2.5 * sd, len(T)))))
        self.LT[L], self.Lr[L], self.Laff[L] = T, r, aff
        self.Lbest[L] = aff.max()
        if parent < 0:
            self.sail[L] = 0.05 * self.seaf[L]
        self.Lpeople[L] = people
        self.Lparent[L] = parent
        self.Lfounded[L] = self.year
        self.Lhow.append(how)
        base = self.colors[people].astype(float)
        self.Lcol[L] = np.clip(base * rng.uniform(0.6, 1.2) +
                               rng.uniform(-30, 30, 3), 15, 245)
        self.Lseen[L] = set(self.Lseen.get(parent, set()))
        return L

    def similarity(self, a, b):
        """1 for identical lineages; within a people it falls with trait
        distance; between peoples it is capped low (SIM_OTHER)."""
        if a == b:
            return 1.0
        key = (a, b) if a < b else (b, a)
        s = self._sim.get(key)
        if s is None:
            d = float(np.linalg.norm(self.LT[a] - self.LT[b]) + 0.3 *
                      np.linalg.norm(np.log(self.Laff[a]) -
                                     np.log(self.Laff[b])))
            if self.Lpeople[a] == self.Lpeople[b]:
                s = math.exp(-d / SIM_SAME_SCALE)
            else:
                s = SIM_OTHER[0] + SIM_OTHER[1] * math.exp(-d / 0.8)
            self._sim[key] = s
        return s

    def accept(self, a, b, level):
        """Both sides must tolerate `level` x their dissimilarity."""
        need, width = level
        need = need * (1 - self.similarity(a, b))
        return sigmoid((self.tol[a] - need) / width) * \
            sigmoid((self.tol[b] - need) / width)

    # ---- capacity
    def prepare_capacity(self):
        self.Kcell = self.drought.copy()
        self.Kcap[:] = np.inf
        if self.cities:
            cc = np.fromiter(self.cities.keys(), int)
            boost = np.array([1.5 + 2.0 * min(1.5, self.polities[
                self.cities[c]["polity"]]["trade"])
                if self.cities[c]["polity"] in self.polities else 1.5
                for c in cc])
            self.Kcell[cc] *= boost
            adm = np.array([self.admin[self.polities[
                self.cities[c]["polity"]]["lin"]]
                if self.cities[c]["polity"] in self.polities
                else self.admin[max(self.lin[c], 0)] for c in cc])
            self.Kcap[cc] = CITY_POP * (CITY_CAP0 + CITY_CAP1 * adm ** 2)

    def adapt(self, L):
        """0..1: how far farming and metallurgy free a lineage from its
        preferred biomes."""
        return 0.5 * np.clip((self.agri[L] - 0.25) / 0.75, 0, 1) + \
            0.5 * np.clip(self.metal[L] / 2.6, 0, 1)

    def biome_fit(self, L, b):
        """Effective biome affinity of lineages L in biomes b."""
        best = self.Lbest[L]
        k = BIOME_K * (1 - BIOME_ADAPT * self.adapt(L))
        return best * (self.Laff[L, b] / best) ** k

    def Kf(self, L, j):
        """Carrying capacity of cells j for lineages L (broadcast)."""
        W = self.W
        a = self.agri[L]
        tools = 1 + TOOLS[0] * self.iron[L] + TOOLS[1] * self.steel[L]
        dens = W.forage[j] * (1 - a) + W.farm[j] * a * tools
        eat = self.peat[self.Lpeople[L]]
        K = W.area[j] * dens * self.biome_fit(L, W.biome[j]) * \
            self.Kcell[j] * (1 + 0.5 * self.seaf[L] * W.coastal[j]) / eat
        return np.minimum(K, self.Kcap[j] / eat)

    # ---- setup
    def start_sites(self):
        """Place founding groups. A people's `head` (years) is its head
        start: groups of the people with the largest head start found at
        year 0, the rest arrive `max_head - head` years later, each on an
        empty site."""
        W = self.W
        dens = W.forage[None] * 0.5 + W.farm[None] * 0.5
        # founders settle only in their people's best biome(s)
        best = self.paff.max(1, keepdims=True)
        fit = best * (self.paff / best) ** BIOME_K
        fit = np.where(self.paff >= 0.9 * best, fit, 0)
        self.site_score = W.area[None] * dens * fit[:, W.biome]
        groups = [(c, k) for c in range(self.nP)
                  for k in range(self.P[c].get("starts", self.starts))]
        groups = [groups[i] for i in self.rng.permutation(len(groups))]
        self.chosen, self.first_site = [], {}
        self.sep0 = float(np.clip(3500 / math.sqrt(len(groups)), 500, 1800))
        H = max(p.get("head", 0) for p in self.P)
        self.arrivals = sorted(
            ((H - self.P[c].get("head", 0), c, k) for c, k in groups),
            key=lambda x: x[0])
        if self.start_mode == "wander":
            self.wander_setup(groups)
        self.place_arrivals()

    # ---- wandering founders
    def wander_setup(self, groups):
        """Before the run, each founding group is dropped at a random
        habitable cell and wanders: every step it stays with probability
        min(0.95, suitability / the people's 95th-percentile suitability),
        otherwise it moves to a neighbouring cell chosen in proportion to
        the square of the surrounding land's suitability (biome preference
        x productivity, smoothed over ~3 cells), so groups can sense better
        land beyond their immediate neighbours."""
        W = self.W
        best = self.paff.max(1, keepdims=True)
        fit = best * (self.paff / best) ** BIOME_K
        dens = 0.75 * W.forage + 0.25 * W.farm
        suit = W.area[None] * dens[None] * fit[:, W.biome] * \
            (1 + 0.5 * self.pT[:, TI["seafaring"]][:, None] * W.coastal[None])
        if self.homelands == "continents":
            big = 15e6 if self.nP <= 5 else 4e6
            suit[:, W.landmass_area[W.landmass] < big] = 0
        ref = np.array([np.percentile(s[s > 0], 95) for s in suit])
        self.suit = suit
        look = np.zeros_like(suit)
        g = np.zeros((NY, NX))
        for c in range(self.nP):
            g[:] = 0
            g[W.row, W.col] = suit[c] / ref[c]
            look[c] = ndimage.gaussian_filter(g, 3, mode="wrap")[W.row, W.col]
        self.look = (look + 1e-6) ** 2
        self.pstay = np.minimum(0.95, suit / ref[:, None])
        self.wpos, self.wfrom = {}, {}
        for c, k in groups:
            ok = np.nonzero(suit[c] > 0)[0]
            self.wpos[(c, k)] = self.wfrom[(c, k)] = int(self.rng.choice(ok))
        self.wander(groups, self.wander_steps, avoid=False)

    def wander(self, groups, steps, avoid):
        if not groups:
            return
        W = self.W
        cs = np.array([c for c, _ in groups])
        pos = np.array([self.wpos[g] for g in groups])
        for _ in range(steps):
            q = self.pstay[cs, pos]
            if avoid:
                q = np.where(self.lin[pos] >= 0, 0, q)
            move = self.rng.random(len(pos)) >= q
            if not move.any():
                continue
            nb = W.nb[pos[move]]
            w = np.where(nb >= 0, self.look[cs[move][:, None],
                                            np.maximum(nb, 0)], 0)
            if avoid:
                w = np.where((nb >= 0) & (self.lin[np.maximum(nb, 0)] < 0),
                             w, 0)
            w = np.where(w.sum(1, keepdims=True) > 0, w,
                         (nb >= 0).astype(float))
            tot = w.sum(1)
            pick = (w.cumsum(1) < (self.rng.random(len(nb)) * tot)[:, None]
                    ).sum(1)
            pick = np.minimum(pick, 7)
            new = nb[np.arange(len(nb)), pick]
            idx = np.nonzero(move)[0]
            good = (new >= 0) & (tot > 0)
            pos[idx[good]] = new[good]
        for g, p in zip(groups, pos):
            self.wpos[g] = int(p)

    def place_arrivals(self):
        while self.arrivals and self.arrivals[0][0] <= self.year:
            _, c, k = self.arrivals.pop(0)
            self.found_group(c, k)
        if self.start_mode == "wander" and self.arrivals:
            # groups not yet arrived keep wandering, avoiding settled land
            self.wander([(c, k) for _, c, k in self.arrivals], 3, avoid=True)

    def empty_near(self, i, c, rings=8):
        """Best empty cell within `rings` steps of i, or -1."""
        W = self.W
        seen, front = {i}, [i]
        for _ in range(rings):
            nxt = []
            for x in front:
                for j in W.nb[x]:
                    if j >= 0 and j not in seen:
                        seen.add(int(j))
                        nxt.append(int(j))
            front = nxt
            cand = [j for j in front if self.lin[j] < 0 and
                    self.suit[c, j] > 0]
            if cand:
                return max(cand, key=lambda j: self.suit[c, j])
        return -1

    def found_group(self, c, k):
        W = self.W
        p = self.P[c]
        i = -1
        if self.start_mode == "wander" and not (p.get("start") and k == 0):
            i = self.wpos[(c, k)]
            if self.lin[i] >= 0:
                i = self.empty_near(i, c)
        if i >= 0:
            pass
        elif p.get("start") and k == 0:
            lon, lat = p["start"]
            i = int(np.argmin(np.linalg.norm(
                W.xyz - unit_xyz(np.array(lon), np.array(lat)), axis=1)))
        else:
            s0 = self.site_score[c].copy()
            s0[self.lin >= 0] = 0
            if self.homelands == "continents":
                big = 15e6 if self.nP <= 5 else 4e6
                s0[W.landmass_area[W.landmass] < big] = 0
            if p["seafaring"] < 0.5:
                s0[W.coastal] *= 0.5
            if self.cluster_km > 0 and c in self.first_site:
                s0[gc_km(W.xyz, self.first_site[c], np.arange(W.N)) >
                   self.cluster_km] = 0
            sep_km = self.sep0
            while True:
                s = s0.copy()
                for j in self.chosen:
                    s[gc_km(W.xyz, j, np.arange(W.N)) < sep_km] = 0
                pos = np.nonzero(s > 0)[0]
                if len(pos) or sep_km < 100:
                    break
                sep_km *= 0.7
            if not len(pos):
                pos = np.nonzero(s0 > 0)[0]
                s = s0
            if not len(pos):
                self.log("origin", f"{p['label']} group {k + 1} finds no "
                         "empty land and never arrives")
                return
            n = max(60, int(self.start_pool * len(pos)))
            top = pos[np.argsort(s[pos])[-n:]]
            i = int(self.rng.choice(top, p=s[top] / s[top].sum()))
        self.first_site.setdefault(c, i)
        self.chosen.append(i)
        L = self.new_lineage(c, -1, "start", sd=self.start_vary)
        self.Lseen[L] = {W.landmass[i]}
        self.Pblk[c].add(int(self.blk[i]))
        self.cul[i], self.lin[i], self.pop[i] = c, L, 400.0
        moved = ""
        if (c, k) in getattr(self, "wfrom", {}):
            d = gc_km(W.xyz, self.wfrom[(c, k)], np.array([i]))[0]
            moved = f", after wandering from {self.place(self.wfrom[(c, k)])}" \
                f" ({d:.0f} km)"
        self.log("origin", f"{p['label']} group {k + 1} {self.lname(L)} "
                 f"founded at {self.place(i)} [{BIOMES[W.biome[i]]}]{moved}")

    # ---- step pieces
    def grow(self):
        occ = np.nonzero(self.lin >= 0)[0]
        L = self.lin[occ]
        k = np.maximum(self.Kf(L, occ), 1e-3)
        p = self.pop[occ]
        # frontier fecundity: thinly settled land grows fastest
        r = self.Lr[L] * (0.6 + 0.4 * self.agri[L]) * \
            (1 + 1.5 * np.clip(1 - 2 * p / k, 0, 1))
        e = np.exp(-r * DT)
        self.pop[occ] = k * p / (p + (k - p) * e)

    def adjacency_by_people(self):
        W = self.W
        adj = np.zeros((self.nP, W.N), bool)
        for k in range(8):
            j = W.nb[:, k]
            cn = np.where(j >= 0, self.cul[np.maximum(j, 0)], -1)
            for c in range(self.nP):
                adj[c] |= cn == c
        return adj

    def migrate(self):
        """Within a lineage, people drift toward room; empty land is taken
        by budding, pioneer leaps and voyages."""
        W, N = self.W, self.W.N
        ar = np.arange(N)
        occ = self.lin >= 0
        was = occ.copy()
        L = np.where(occ, self.lin, 0)
        c = self.Lpeople[L]
        press = self.pop / np.maximum(self.Kf(L, ar), 1e-3)
        adj = self.adjacency_by_people()
        nadj = adj.sum(0)
        expn, sep = self.expn[L], self.sep[L]
        thr = 0.9 - 0.6 * expn
        frac = 0.04 + 0.3 * expn * np.clip(press - thr, 0, 1.5)
        E = np.where(occ, self.pop * frac, 0)
        w = np.zeros((N, 8))
        for k in range(8):
            j = W.nb[:, k]
            jj = np.maximum(j, 0)
            ok = occ & (j >= 0) & (self.lin[jj] == L)
            Kt = np.maximum(self.Kf(L, jj), 1e-3)
            room = np.clip(1 - self.pop[jj] / Kt, 0, 1)
            foreign = (nadj[jj] - adj[c, jj]) > 0
            w[:, k] = ok * room * np.sqrt(Kt) / W.edgecost[:, k] * \
                (1 - 0.9 * sep * foreign)
        Wsum = w.sum(1)
        go = Wsum > 0
        E = np.where(go, E, 0)
        self.pop -= E
        F = (E[:, None] * w / np.where(go, Wsum, 1)[:, None]).ravel()
        tgt = W.nb.ravel()
        m = (tgt >= 0) & (F > 0)
        np.add.at(self.pop, tgt[m], F[m])
        for _ in range(2):
            occ = self.lin >= 0
            L = np.where(occ, self.lin, 0)
            press = self.pop / np.maximum(self.Kf(L, ar), 1e-3)
            adj = self.adjacency_by_people()
            self.settle(*self.budding(press, adj, adj.sum(0), L, occ))
        self.pioneers(press)
        self.voyages(press)
        self.settler_lineages(np.nonzero((self.lin >= 0) & ~was)[0])

    def settler_lineages(self, new):
        """Settlers entering a region (BLOCK x BLOCK cells) their people
        has never held found a daughter lineage: the parent's traits with a
        small mutation."""
        if not len(new) or self.settle_drift <= 0:
            return
        new = new[self.Lfounded[self.lin[new]] != self.year]
        for L, cells in self.by_lineage(new):
            seen = self.Pblk[self.Lpeople[L]]
            b = self.blk[cells]
            for bb in np.unique(b):
                if int(bb) in seen:
                    continue
                seen.add(int(bb))
                D = self.new_lineage(self.Lpeople[L], L, "settler",
                                     sd=self.settle_drift)
                self.lin[cells[b == bb]] = D

    def budding(self, press, adj, nadj, L, occ):
        """A crowded cell splits off one band toward its best empty
        neighbour. Expansive lineages split before they are full."""
        W, N = self.W, self.W.N
        c = self.Lpeople[L]
        thr = 0.45 - 0.35 * self.expn[L]
        can = occ & (press > thr) & (self.pop > 2 * FOUND_MIN)
        best = np.zeros(N)
        tgt = -np.ones(N, int)
        noise = self.rng.uniform(0.6, 1.4, (N, 8))
        for k in range(8):
            j = W.nb[:, k]
            jj = np.maximum(j, 0)
            ok = can & (j >= 0) & (self.lin[jj] < 0)
            Kt = self.Kf(L, jj)
            foreign = (nadj[jj] - adj[c, jj]) > 0
            s = ok * np.sqrt(np.maximum(Kt, 0)) / W.edgecost[:, k] * \
                W.colonize[jj] * (1 + RIV_BUD * (W.river & W.river[jj])) * \
                (1 - 0.95 * self.sep[L] * foreign) * noise[:, k] * \
                (Kt > 2 * FOUND_MIN)
            better = s > best
            best = np.where(better, s, best)
            tgt = np.where(better, j, tgt)
        src = np.nonzero(tgt >= 0)[0]
        Ls = L[src]
        band = np.maximum(FOUND_MIN, (0.2 + 0.25 * self.expn[Ls]) *
                          self.pop[src])
        band = np.minimum(np.maximum(band, 0.15 * self.Kf(Ls, tgt[src])),
                          0.5 * self.pop[src])
        self.pop[src] -= band
        return src, tgt[src], band, Ls

    def settle(self, src, tgt, band, bl):
        """Bands claim empty cells; the largest claimant wins, the rest
        go home."""
        if not len(src):
            return
        order = np.lexsort((-band, tgt))
        src, tgt, band, bl = src[order], tgt[order], band[order], bl[order]
        first = np.ones(len(tgt), bool)
        first[1:] = tgt[1:] != tgt[:-1]
        win = first & (self.lin[tgt] < 0)
        self.lin[tgt[win]] = bl[win]
        self.cul[tgt[win]] = self.Lpeople[bl[win]]
        self.pop[tgt[win]] = band[win]
        np.add.at(self.pop, src[~win], band[~win])

    def by_lineage(self, cells):
        """Group cell indices by lineage: yields (L, cells of L)."""
        if not len(cells):
            return
        Ls = self.lin[cells]
        o = np.argsort(Ls, kind="stable")
        cells, Ls = cells[o], Ls[o]
        u, start = np.unique(Ls, return_index=True)
        ends = list(start[1:]) + [len(cells)]
        for L, a, b in zip(u, start, ends):
            yield int(L), cells[a:b]

    def pioneers(self, press):
        """Bands leap past the frontier into empty land 2-6 cells away."""
        W = self.W
        eat = self.peat[np.maximum(self.cul, 0)]
        cand = np.nonzero((self.lin >= 0) & (self.pop * eat > 300))[0]
        for L, cells in self.by_lineage(cand):
            lam = 3.0 * self.expn[L] ** 2 * (1 + math.log10(1 + len(cells)))
            n = self.rng.poisson(lam)
            if not n:
                continue
            wts = self.pop[cells] * np.clip(press[cells], 0.05, 2)
            for s in self.rng.choice(cells, n, p=wts / wts.sum()):
                if W.river[s] and self.rng.random() < RIV_LEAP:
                    self.river_leap(L, s)
                    continue
                dr, dc = self.rng.integers(-6, 7, 2)
                if max(abs(dr), abs(dc)) < 2:
                    continue
                r2, c2 = W.row[s] + dr, (W.col[s] + dc) % NX
                if not (0 <= r2 < NY):
                    continue
                t = W.idx2[r2, c2]
                if t < 0 or self.lin[t] >= 0 or \
                        self.rng.random() > W.colonize[t] or \
                        W.landmass[t] != W.landmass[s] or \
                        self.Kf(L, t) * self.peat[self.Lpeople[L]] < 200:
                    continue
                mv = min(120.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
                self.pop[s] -= mv
                self.lin[t], self.cul[t], self.pop[t] = L, self.Lpeople[L], mv

    def river_leap(self, L, s):
        """A band travels along the river network from s and settles an
        empty cell on the way."""
        W = self.W
        n = int(RIV_STEPS[0] + RIV_STEPS[1] * self.sail[L])
        downstream = self.rng.random() < 0.5
        x, path = s, []
        for _ in range(n):
            if downstream:
                x = int(W.down[x])
            else:
                ups = W.up[x]
                if not ups:
                    break
                q = W.Q[ups] + 1
                x = int(self.rng.choice(ups, p=q / q.sum()))
            if x < 0:
                break
            path.append(x)
        cand = [t for t in path[1:] if self.lin[t] < 0]
        if not cand:
            return
        t = int(self.rng.choice(cand))
        if self.rng.random() > W.colonize[t] or \
                self.Kf(L, t) * self.peat[self.Lpeople[L]] < 200:
            return
        mv = min(120.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
        self.pop[s] -= mv
        self.lin[t], self.cul[t], self.pop[t] = L, self.Lpeople[L], mv

    def sail_km(self, L):
        """Typical voyage distance (km) of lineage L."""
        return SAIL_D0 + SAIL_D1 * self.sail[L] ** 1.5

    def voyages(self, press):
        """Sea colonization from crowded coasts to empty coasts. Targets
        are weighted by exp(-distance / sail_km), so sailing sets how far
        colonists usually go rather than whether they can go at all.
        A colony on a landmass new to its lineage founds a daughter
        lineage (founder effect)."""
        W = self.W
        eat = self.peat[np.maximum(self.cul, 0)]
        cand = np.nonzero((self.lin >= 0) & W.coastal & (self.pop * eat > 400) &
                          (press > 0.5))[0]
        for L, src in self.by_lineage(cand):
            D = self.sail_km(L)
            lam = 2.5 * self.seaf[L] * (0.1 + self.sail[L]) * \
                math.sqrt(len(src))
            n = self.rng.poisson(lam)
            for s in self.rng.choice(src, min(n, 6)):
                ids = W.coast_tree.query_ball_point(
                    W.xyz[s], 2 * math.sin(min(4 * D, 9000) / R_EARTH / 2))
                cnd = W.coast_idx[ids]
                cnd = cnd[self.lin[cnd] < 0]
                if not len(cnd):
                    continue
                wt = self.Kf(L, cnd)
                ok = wt * self.peat[self.Lpeople[L]] > 300
                cnd, wt = cnd[ok], wt[ok]
                if not len(cnd):
                    continue
                wt = wt * np.exp(-gc_km(W.xyz, s, cnd) / D) * W.colonize[cnd]
                if wt.sum() <= 0:
                    continue
                t = int(self.rng.choice(cnd, p=wt / wt.sum()))
                mv = min(200.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
                self.pop[s] -= mv
                lm = W.landmass[t]
                Lt = L
                if lm not in self.Lseen[L]:
                    self.Lseen[L].add(lm)
                    if W.landmass_area[lm] > 2e5:
                        Lt = self.new_lineage(self.Lpeople[L], L, "colony",
                                              sd=self.drift)
                        self.Lseen[Lt] = {lm}
                        self.log("voyage", f"{self.lname(L)} sailors land "
                                 f"on a new landmass at {self.place(t)} "
                                 f"({W.landmass_area[lm]/1e6:.1f}M km2), "
                                 f"founding {self.lname(Lt)}")
                self.lin[t], self.cul[t], self.pop[t] = \
                    Lt, self.Lpeople[Lt], mv

    def raids(self):
        """Cell-scale violence where peoples touch outside state control."""
        W = self.W
        a, b = W.E1, W.E2
        ca, cb = self.cul[a], self.cul[b]
        mix = (ca >= 0) & (cb >= 0) & (ca != cb)
        a, b, ca, cb = a[mix], b[mix], ca[mix], cb[mix]
        if not len(a):
            return
        for x, y in set(zip(ca.tolist(), cb.tolist())):
            if not self.contact_seen[x, y]:
                self.contact_seen[x, y] = self.contact_seen[y, x] = True
                self.log("contact", f"first contact: {self.keys[x]} meets "
                         f"{self.keys[y]}")
        for att, dfn in ((a, b), (b, a)):
            La, Ld = self.lin[att], self.lin[dfn]
            pa = self.pop[att] / np.maximum(self.Kf(La, att), 1e-3)
            same_state = (self.cell_pol[att] >= 0) & \
                (self.cell_pol[att] == self.cell_pol[dfn])
            p = DT * 0.02 * self.viol[La] * (0.5 + pa) * \
                (1 + self.sep[La]) * (1 - 0.5 * self.tol[La]) * \
                np.where(same_state, 0.2, 1)
            hit = self.rng.random(len(att)) < np.clip(p, 0, 0.9)
            rel = np.sqrt(self.psize[self.cul[att]] / self.psize[self.cul[dfn]])
            self.pop[dfn[hit]] *= 1 - np.clip(
                0.12 * self.viol[La[hit]] * rel[hit] / W.defence[dfn[hit]],
                0, 0.6)
            self.pop[att[hit]] *= 0.99
            pd = self.pop[dfn] / np.maximum(self.Kf(Ld, dfn), 1e-3)
            take = hit & (pd < 0.15) & (pa > 0.6) & \
                (self.rng.random(len(att)) < self.viol[La])
            ti, first = np.unique(dfn[take], return_index=True)
            si = att[take][first]
            mv = 0.25 * self.pop[si]
            self.pop[si] -= mv
            self.lin[ti] = self.lin[si]
            self.cul[ti] = self.cul[si]
            self.pop[ti] = mv

    def tidy(self):
        dead = (self.pop < 5) & (self.lin >= 0)
        self.pop[dead] = 0
        self.cul[dead] = -1
        self.lin[dead] = -1

    # ---- cities and polities
    def new_polity(self, L, capital, cohesion=0.6, parent=None):
        pid = self.next_pid
        self.next_pid += 1
        c = int(self.Lpeople[L])
        self.polities[pid] = dict(id=pid, culture=c, lin=int(L),
                                  capital=capital, founded=self.year,
                                  ended=None, cohesion=cohesion, trade=0.0,
                                  cities={capital}, peak_cells=0,
                                  peak_year=self.year, peak_cities=1,
                                  peak_pop=0, peak_mask=None, peoples=set(),
                                  parent=parent, n_cells=0, strength=0,
                                  pop=0, col=self.polity_color(c))
        return pid

    def polity_color(self, c):
        base = self.colors[c].astype(float)
        wide = self.nP <= 5
        j = self.rng.uniform(0.55, 1.25) if wide else \
            self.rng.uniform(0.7, 1.15)
        h = self.rng.uniform(-28, 28, 3) if wide else \
            self.rng.uniform(-15, 15, 3)
        return np.clip(base * j + h, 20, 245).astype(np.uint8)

    def end_city(self, cell, why):
        rec = self.cities.pop(cell)
        rec["ended"] = self.year
        rec["end_reason"] = why
        p = self.polities.get(rec["polity"])
        if p:
            p["cities"].discard(cell)
            if p["capital"] == cell:
                self.recapital(p)

    def recapital(self, p):
        if not p["cities"]:
            self.kill_polity(p["id"], "lost its last city")
            return
        p["capital"] = max(p["cities"], key=lambda x: self.pop[x])

    def kill_polity(self, pid, why):
        p = self.polities.get(pid)
        if p is None or p["ended"] is not None:
            return
        p["ended"] = self.year
        if p["peak_cities"] >= 3 or p["peak_cells"] >= 150:
            self.log("fall", f"{self.pname(pid)} falls ({why}); "
                     f"{self.year - p['founded']} yrs, peak "
                     f"{p['peak_cities']} cities / {p['peak_cells']} cells")
        for d in (self.wars, self.ties, self.allies):
            for key in [k for k in d if pid in k]:
                del d[key]
        for c in list(p["cities"]):
            self.cities.get(c, {}).update(polity=-1)
        p["cities"] = set()

    def update_cities(self):
        W = self.W
        for cell in list(self.cities):
            rec = self.cities[cell]
            if self.cul[cell] != rec["culture"]:
                self.end_city(cell, "people replaced")
            elif self.pop[cell] < CITY_KEEP * self.pcity[rec["culture"]]:
                self.end_city(cell, "depopulated")
        pot2 = np.zeros((NY, NX))
        occ = self.lin >= 0
        fpop = np.where(occ, self.pop * self.peat[np.maximum(self.cul, 0)], 0)
        pot = fpop * W.locus
        pot2[W.row, W.col] = pot
        mx = ndimage.maximum_filter(pot2, size=5, mode="wrap")
        taken = np.zeros((NY, NX), bool)
        if self.cities:
            cc = np.fromiter(self.cities.keys(), int)
            taken[W.row[cc], W.col[cc]] = True
            taken = ndimage.binary_dilation(taken, np.ones((5, 5)))
        cand = np.nonzero(occ & (self.pop > self.pcity[np.maximum(
            self.cul, 0)]) &
                          (pot >= mx[W.row, W.col]) &
                          ~taken[W.row, W.col])[0]
        for cell in cand:
            c, L = int(self.cul[cell]), int(self.lin[cell])
            owner = int(self.cell_pol[cell])
            op = self.polities.get(owner)
            join = False
            if op is not None and op["ended"] is None:
                if op["culture"] == c:
                    join = self.rng.random() < \
                        0.3 + 0.7 * self.state[op["lin"]]
                else:
                    join = self.rng.random() < 0.7
            rec = dict(cell=int(cell), culture=c, founded=self.year,
                       ended=None, end_reason="", peak=0.0, polity=-1,
                       lon=float(W.lon[cell]), lat=float(W.lat[cell]),
                       owners=[])
            self.cities[cell] = rec
            self.city_hist.append(rec)
            if join:
                rec["polity"] = owner
                op["cities"].add(cell)
            else:
                rec["polity"] = self.new_polity(L, cell)
            rec["owners"].append(rec["polity"])
            self.first(("city", c), "city", f"first city of {self.keys[c]} "
                       f"at {self.place(cell)}")

    def territory(self):
        W = self.W
        self.cell_pol[:] = -1
        self.cell_city[:] = -1
        if not self.cities:
            return
        cc = np.fromiter(self.cities.keys(), int)
        dist, _, src = dijkstra(W.G, indices=cc, min_only=True,
                                return_predecessors=True,
                                limit=REACH0 + REACH1 + 1)
        ok = src >= 0
        si = np.where(ok, src, 0)
        cpol = np.full(W.N, -1)
        cpol[cc] = [self.cities[c]["polity"] for c in cc]
        creach = np.zeros(W.N)
        creach[cc] = [REACH0 + REACH1 * self.admin[
            self.polities[self.cities[c]["polity"]]["lin"]]
            if self.cities[c]["polity"] in self.polities else REACH0
            for c in cc]
        ok &= dist <= creach[si]
        self.cell_city[ok] = src[ok]
        self.cell_pol[ok] = cpol[src[ok]]

    def polity_stats(self):
        W = self.W
        n = self.next_pid
        pol = self.cell_pol
        m = pol >= 0
        Lpop = np.bincount(self.lin[self.lin >= 0],
                           weights=self.pop[self.lin >= 0], minlength=self.nL)
        pc = np.full(n, -1)
        pl = np.zeros(n, int)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                # a ruling lineage that has died out passes to the capital's
                cap = p["capital"]
                if Lpop[p["lin"]] <= 0 and self.lin[cap] >= 0:
                    p["lin"] = int(self.lin[cap])
                    p["culture"] = int(self.cul[cap])
                pc[pid], pl[pid] = p["culture"], p["lin"]
        own = m & (self.cul == pc[np.maximum(pol, 0)])
        tolp = self.tol[pl[np.maximum(pol, 0)]]
        popw = np.where(own, self.pop, (0.4 + 0.5 * tolp) * self.pop) * \
            self.psize[np.maximum(self.cul, 0)]
        pop_by = np.bincount(pol[m], weights=self.pop[m], minlength=n)
        str_by = np.bincount(pol[m], weights=popw[m], minlength=n)
        cells_by = np.bincount(pol[m], minlength=n)
        area_by = np.bincount(pol[m], weights=W.area[m], minlength=n)
        # assimilation: kin under a ruling lineage slowly take it on
        rl = pl[np.maximum(pol, 0)]
        kin = m & own & (self.lin >= 0) & (self.lin != rl)
        conv = kin & (self.rng.random(W.N) <
                      DT * 0.008 * (0.5 + self.state[rl]))
        self.lin[conv] = rl[conv]
        # borders
        pa, pb = pol[W.E1], pol[W.E2]
        frontier = np.zeros(n)
        border = np.zeros(n)
        for x, y, cy in ((pa, pb, self.cul[W.E2]), (pb, pa, self.cul[W.E1])):
            b = (x >= 0) & (x != y)
            np.add.at(border, x[b], 1)
            f = b & (cy >= 0) & (cy != pc[np.maximum(x, 0)])
            np.add.at(frontier, x[f], 1)
        adjm = (pa >= 0) & (pb >= 0) & (pa != pb)
        lo, hi = np.minimum(pa[adjm], pb[adjm]), np.maximum(pa[adjm],
                                                           pb[adjm])
        keys = np.unique(lo.astype(np.int64) * 10_000_000 + hi)
        self.adj = {(int(k // 10_000_000), int(k % 10_000_000))
                    for k in keys}
        self.adj |= self.sea_adjacency()
        for pid, p in self.polities.items():
            if p["ended"] is not None:
                continue
            L = p["lin"]
            mil = (0.5 + self.viol[L]) * (1 + METAL_MIL[0] * self.bronze[L] +
                                         METAL_MIL[1] * self.iron[L] +
                                         METAL_MIL[2] * self.steel[L])
            p["pop"] = pop_by[pid]
            p["n_cells"] = int(cells_by[pid])
            p["km2"] = float(area_by[pid])
            p["strength"] = str_by[pid] * mil * (0.3 + 0.7 * p["cohesion"])
            ff = frontier[pid] / max(border[pid], 1)
            S = p["cohesion"]
            nc = len(p["cities"])
            age = self.year - p["founded"]
            dS = 0.04 * self.coh[L] * S * (1 - S) * (0.3 + ff) - \
                0.004 * S * (1 + 0.5 * math.log1p(nc)) * (1 + age / 600)
            p["cohesion"] = float(np.clip(S + DT * dS, 0.02, 1))
            if p["n_cells"] > p["peak_cells"]:
                p["peak_cells"] = p["n_cells"]
                p["peak_year"] = self.year
                if p["n_cells"] >= 120:
                    p["peak_mask"] = np.nonzero(pol == pid)[0]
            p["peak_cities"] = max(p["peak_cities"], nc)
            p["peak_pop"] = max(p["peak_pop"], p["pop"])
            for x in p["cities"]:
                p["peoples"].add(self.cities[x]["culture"])

    def sea_adjacency(self):
        """Polities whose coastal cities lie within a sailor's range."""
        W = self.W
        if self.tick % 4 and hasattr(self, "_sea_adj"):
            return {k for k in self._sea_adj
                    if all(self.polities.get(x, {}).get("ended", 1) is None
                           for x in k)}
        out = set()
        cc = [c for c in self.cities if W.coastal[c] and
              self.cities[c]["polity"] in self.polities]
        if len(cc) > 1:
            cc = np.array(cc)
            tree = cKDTree(W.xyz[cc])
            for c in cc:
                pid = self.cities[c]["polity"]
                rng_km = 2 * self.sail_km(self.polities[pid]["lin"])
                for j in tree.query_ball_point(
                        W.xyz[c], 2 * math.sin(rng_km / R_EARTH / 2)):
                    q = self.cities[cc[j]]["polity"]
                    if q != pid and q in self.polities:
                        out.add((min(pid, q), max(pid, q)))
        self._sea_adj = out
        return out

    def live(self, k):
        a, b = self.polities.get(k[0]), self.polities.get(k[1])
        if not a or not b or a["ended"] is not None or b["ended"] is not None:
            return None
        return a, b

    def trade_ties(self):
        """Trade grows with both sides' trade drive and tolerance, gated by
        whether each tolerates the other's difference."""
        for k in list(self.ties):
            if k not in self.adj or k in self.wars or not self.live(k):
                self.ties[k] *= 0.9
                if self.ties[k] < 0.02:
                    del self.ties[k]
        W = self.W
        riv = {}
        for pid, p in self.polities.items():
            if p["ended"] is None and p["cities"]:
                cc = np.fromiter(p["cities"], int)
                rc = cc[W.river[cc]]
                riv[pid] = (len(rc) / len(cc), set(W.basin[rc].tolist()))
        for k in self.adj:
            if k in self.wars:
                continue
            ab = self.live(k)
            if not ab:
                continue
            La, Lb = ab[0]["lin"], ab[1]["lin"]
            ra, ba = riv.get(k[0], (0.0, set()))
            rb, bb = riv.get(k[1], (0.0, set()))
            g = self.trade[La] * self.trade[Lb] * \
                (0.4 + 0.3 * (self.tol[La] + self.tol[Lb])) * \
                self.accept(La, Lb, TOL_TRADE) * \
                (1 + RIV_TRADE * (ra + rb) / 2) * \
                (1 + BASIN_TRADE * bool(ba & bb))
            t = self.ties.get(k, 0.0)
            self.ties[k] = t + DT * 0.03 * g * (1 - t)
        for (x, y), t in self.ties.items():
            cx, cy = self.polities[x]["culture"], self.polities[y]["culture"]
            if cx != cy and t > 0.5 and not self.trade_seen[cx, cy]:
                self.trade_seen[cx, cy] = self.trade_seen[cy, cx] = True
                self.log("trade", f"lasting trade between {self.keys[cx]} "
                         f"and {self.keys[cy]}: {self.pname(x)} and "
                         f"{self.pname(y)}")
        tot = {}
        for (x, y), t in self.ties.items():
            tot[x] = tot.get(x, 0) + t
            tot[y] = tot.get(y, 0) + t
        for pid, p in self.polities.items():
            p["trade"] = tot.get(pid, 0.0)

    def diplomacy(self):
        """Alliances form between neighbours who tolerate each other; long
        alliances can fuse into one state. Within a people moderate
        tolerance suffices; across peoples both must be highly tolerant."""
        rng = self.rng
        for k in list(self.allies):
            ab = self.live(k)
            if not ab or k in self.wars:
                self.allies.pop(k, None)
                continue
            La, Lb = ab[0]["lin"], ab[1]["lin"]
            if rng.random() < DT * 0.004 * (1 - self.accept(La, Lb,
                                                              TOL_ALLY)):
                self.allies.pop(k, None)
        for k in self.adj:
            if k in self.wars or k in self.allies:
                continue
            ab = self.live(k)
            if not ab:
                continue
            a, b = ab
            La, Lb = a["lin"], b["lin"]
            p = DT * 0.005 * self.accept(La, Lb, TOL_ALLY) * \
                (0.3 + self.ties.get(k, 0.0))
            if rng.random() < p:
                self.allies[k] = self.year
                cross = a["culture"] != b["culture"]
                if cross or len(a["cities"]) + len(b["cities"]) >= 8:
                    self.log("alliance", f"{self.pname(k[0])} and "
                             f"{self.pname(k[1])} ally")
        for k in list(self.allies):
            ab = self.live(k)
            if not ab or self.ties.get(k, 0) < 0.3:
                continue
            a, b = ab
            La, Lb = a["lin"], b["lin"]
            p = DT * 0.0025 * self.accept(La, Lb, TOL_FUSE) * \
                0.5 * (self.state[La] + self.state[Lb])
            if rng.random() < p:
                self.fuse(a, b)

    def fuse(self, a, b):
        big, small = (a, b) if a["pop"] >= b["pop"] else (b, a)
        for x in small["cities"]:
            self.cities[x]["polity"] = big["id"]
            self.cities[x]["owners"].append(big["id"])
        big["cities"] |= small["cities"]
        big["peoples"] |= small["peoples"]
        small["cities"] = set()
        big["cohesion"] = max(big["cohesion"], small["cohesion"])
        cross = a["culture"] != b["culture"]
        self.blend(big, small)
        if cross:
            self.log("fusion", f"{self.pname(small['id'])} and "
                     f"{self.pname(big['id'])} fuse into one state "
                     f"({self.keys[small['culture']]} + "
                     f"{self.keys[big['culture']]}) under "
                     f"{self.lname(big['lin'])}")
        elif len(big["cities"]) >= 5:
            self.log("union", f"{self.pname(small['id'])} joins "
                     f"{self.pname(big['id'])} by treaty")
        self.kill_polity(small["id"], f"{'fusion' if cross else 'union'} "
                         f"with {self.pname(big['id'])}")

    def blend(self, big, small):
        """A merged state takes one culture: its ruling lineages are
        replaced, inside its territory, by new lineages whose cultural
        traits are the population-weighted average of the two (technology:
        the better of the two). Growth rate, biome fit and body size stay
        with each people."""
        La, Lb = big["lin"], small["lin"]
        if La == Lb:
            return
        ids = (big["id"], small["id"])
        cells = np.nonzero(np.isin(self.cell_pol, ids) &
                           np.isin(self.lin, (La, Lb)))[0]
        wa = self.pop[cells][self.lin[cells] == La].sum() + 1
        wb = self.pop[cells][self.lin[cells] == Lb].sum() + 1
        T = (wa * self.LT[La] + wb * self.LT[Lb]) / (wa + wb)
        how = "fusion" if big["culture"] != small["culture"] else "union"
        new = {}
        for Lo in (La, Lb):
            c = int(self.Lpeople[Lo])
            if c in new:
                continue
            D = self.new_lineage(c, Lo, how)
            if D == Lo:
                return
            self.LT[D] = T
            for t in ("agri", "metal", "sail", "admin"):
                v = getattr(self, t)
                v[D] = max(v[La], v[Lb])
            for t in ("bronze", "iron", "steel"):
                v = getattr(self, t)
                v[D] = v[La] or v[Lb]
            self.Lseen[D] = self.Lseen[La] | self.Lseen[Lb]
            new[c] = D
        for Lo in (La, Lb):
            self.lin[cells[self.lin[cells] == Lo]] = new[int(self.Lpeople[Lo])]
        big["lin"] = new[int(big["culture"])]

    def city_dist(self, a, b):
        return float(gc_km(self.W.xyz, a, np.array([b]))[0])

    def projected(self, P, t):
        reach = REACH0 + REACH1 * self.admin[P["lin"]]
        return P["strength"] * math.exp(-self.city_dist(P["capital"], t) /
                                        (1.5 * reach))

    def wars_step(self):
        rng = self.rng
        for k in self.adj:
            if k in self.wars or k in self.allies or \
                    self.truce.get(k, -1) > self.tick:
                continue
            ab = self.live(k)
            if not ab:
                continue
            for att, dfn in (k, k[::-1]):
                A, B = self.polities[att], self.polities[dfn]
                La, Lb = A["lin"], B["lin"]
                ratio = A["strength"] / max(B["strength"], 1)
                rf = min(3.0, ratio) ** 1.2 / 2
                xeno = 0.5 + (1 - self.similarity(La, Lb)) * \
                    (1 + 1.5 * self.sep[La])
                p = DT * 0.012 * self.viol[La] * A["cohesion"] * rf * xeno * \
                    (1 - self.ties.get(k, 0.0)) * (1 - 0.4 * self.tol[La])
                if rng.random() < min(p, 0.5):
                    self.wars[k] = dict(att=att, dfn=dfn, start=self.tick,
                                        caps=0)
                    self.ties.pop(k, None)
                    if len(A["cities"]) + len(B["cities"]) >= 8:
                        self.log("war", f"{self.pname(att)} attacks "
                                 f"{self.pname(dfn)}")
                    break
        for k in list(self.wars):
            w = self.wars.get(k)
            if w is None:
                continue
            A, B = self.polities.get(w["att"]), self.polities.get(w["dfn"])
            if not A or not B or A["ended"] is not None or \
                    B["ended"] is not None or not B["cities"] \
                    or not A["cities"]:
                self.wars.pop(k, None)
                continue
            targets = list(B["cities"])
            dists = gc_km(self.W.xyz, A["capital"], np.array(targets))
            t = targets[int(np.argmin(dists))]
            PA = self.projected(A, t)
            PB = self.projected(B, t)
            # defensive allies send help (not against their own allies)
            for kk in self.allies:
                if w["dfn"] in kk:
                    q = kk[1] if kk[0] == w["dfn"] else kk[0]
                    Q = self.polities.get(q)
                    if q != w["att"] and Q and Q["ended"] is None and \
                            (min(q, w["att"]), max(q, w["att"])) \
                            not in self.allies:
                        PB += 0.35 * self.projected(Q, t)
            PB *= 1.4 * self.W.defence[t] * \
                (1.25 if t == B["capital"] else 1)
            pw = PA ** 2 / (PA ** 2 + PB ** 2 + 1e-9)
            self.pop[t] *= 0.97
            if rng.random() < pw:
                self.capture(w["att"], w["dfn"], t)
                w["caps"] += 1
            else:
                A["cohesion"] *= 0.98
            dur = self.tick - w["start"]
            if rng.random() < 0.12 + 0.03 * dur or \
                    self.polities[w["dfn"]]["ended"] is not None:
                self.wars.pop(k, None)
                self.truce[k] = self.tick + 6

    def capture(self, att, dfn, t):
        A, B = self.polities[att], self.polities[dfn]
        ca, La = A["culture"], A["lin"]
        rec = self.cities[t]
        was_cap = B["capital"] == t
        B["cities"].discard(t)
        A["cities"].add(t)
        rec["polity"] = att
        rec["owners"].append(att)
        self.pop[t] *= 1 - (0.1 + 0.4 * self.viol[La])
        A["cohesion"] = min(1, A["cohesion"] + 0.03)
        if rec["culture"] != ca and self.rng.random() < \
                self.sep[La] * self.viol[La] * (1 - self.tol[La]):
            hint = (self.cell_city == t) & (self.cul == rec["culture"])
            self.pop[hint] *= 0.15
            self.pop[t] *= 0.3
            if len(A["cities"]) + len(B["cities"]) >= 5:
                self.log("clearance", f"{self.pname(att)} clears "
                         f"{self.keys[rec['culture']]} from the city at "
                         f"{self.place(t)}")
        if was_cap:
            B["cohesion"] *= 0.6
            if len(B["cities"]) + 1 >= 4:
                self.log("conquest", f"{self.pname(att)} takes the capital "
                         f"of {self.pname(dfn)} at {self.place(t)}")
            if not B["cities"]:
                self.kill_polity(dfn, f"conquered by {self.pname(att)}")
            elif B["culture"] == ca and len(B["cities"]) <= 3:
                for c in list(B["cities"]):
                    self.cities[c]["polity"] = att
                    self.cities[c]["owners"].append(att)
                    A["cities"].add(c)
                B["cities"] = set()
                self.kill_polity(dfn, f"absorbed by {self.pname(att)}")
            elif self.rng.random() < 0.4:
                rest = list(B["cities"])
                B["cities"] = set()
                self.kill_polity(dfn, "shattered after its capital fell")
                for c in rest:
                    Lc = self.lin[c] if self.lin[c] >= 0 else B["lin"]
                    self.cities[c]["polity"] = self.new_polity(
                        Lc, c, 0.5, parent=dfn)
                    self.cities[c]["owners"].append(self.cities[c]["polity"])
            else:
                self.recapital(B)

    def rebellions(self):
        rng = self.rng
        for pid in list(self.polities):
            p = self.polities[pid]
            if p["ended"] is not None or len(p["cities"]) < 2:
                continue
            L = p["lin"]
            reach = REACH0 + REACH1 * self.admin[L]
            cities = [x for x in p["cities"] if x != p["capital"]]
            d = gc_km(self.W.xyz, p["capital"], np.array(cities))
            nc = len(p["cities"])
            for x, dx in zip(cities, d):
                if x not in p["cities"] or self.lin[x] < 0:
                    continue
                Lx = int(self.lin[x])
                alien = 1 + 3 * (1 - self.similarity(L, Lx)) * \
                    (1 - 0.6 * self.tol[L])
                pr = DT * 0.0009 * (dx / reach) ** 2 * \
                    (1.5 - p["cohesion"]) * alien * (1 + 0.2 * math.log(nc))
                if rng.random() < pr:
                    self.revolt(pid, x)

    def revolt(self, pid, x):
        """A province breaks away. Rebels of the ruling lineage found a
        daughter lineage (they drift apart from here); rebels of another
        lineage or people restore their own."""
        p = self.polities[pid]
        cx, Lx = self.cities[x]["culture"], int(self.lin[x])
        same = Lx == p["lin"]
        Lnew = self.new_lineage(cx, Lx, "secession", sd=self.drift) \
            if same else Lx
        new = self.new_polity(Lnew, x, 0.75, parent=pid)
        p["cities"].discard(x)
        self.cities[x]["polity"] = new
        self.cities[x]["owners"].append(new)
        group = [x]
        others = [y for y in p["cities"] if y != p["capital"] and
                  self.cities[y]["culture"] == cx]
        if others:
            dn = gc_km(self.W.xyz, x, np.array(others))
            dc = gc_km(self.W.xyz, p["capital"], np.array(others))
            for y, a, b in zip(others, dn, dc):
                if a < 400 and a < b and self.rng.random() < 0.6:
                    p["cities"].discard(y)
                    self.cities[y]["polity"] = new
                    self.cities[y]["owners"].append(new)
                    self.polities[new]["cities"].add(y)
                    group.append(y)
        if same:
            hint = np.isin(self.cell_city, group) & (self.lin == Lx)
            self.lin[hint] = Lnew
        taken = len(group)
        if taken >= 3 or (taken >= 2 and len(p["cities"]) >= 6):
            kind = ("ethnic revolt" if cx != p["culture"] else
                    "secession" if same else "kin revolt")
            extra = f", new lineage {self.lname(Lnew)}" if same else ""
            self.log("revolt", f"{kind}: {self.pname(new)} breaks from "
                     f"{self.pname(pid)} at {self.place(x)} "
                     f"with {taken} cities{extra}")
        p["cohesion"] *= 0.9

    # ---- technology
    def technology(self):
        """Per-lineage invention, plus borrowing from the most advanced
        lineage each one touches (borders, trade, rule)."""
        W, nL = self.W, self.nL
        occ = self.lin >= 0
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        self.Lpeak[:nL] = np.maximum(self.Lpeak[:nL], Lpop)
        dead = (Lpop <= 0) & (self.Lended[:nL] < 0) & (self.Lpeak[:nL] > 0)
        self.Lended[:nL][dead] = self.year
        A = np.nonzero(Lpop > 0)[0]
        if not len(A):
            return
        nA = len(A)
        amap = -np.ones(nL, int)
        amap[A] = np.arange(nA)
        ncity = np.zeros(nL)
        for cell in self.cities:
            if self.lin[cell] >= 0:
                ncity[self.lin[cell]] += 1
        coastal = np.bincount(self.lin[occ], weights=(self.pop * W.coastal)
                              [occ], minlength=nL) / np.maximum(Lpop, 1)
        # contact between lineages
        M = np.zeros((nA, nA))
        la, lb = self.lin[W.E1], self.lin[W.E2]
        m = (la >= 0) & (lb >= 0) & (la != lb)
        np.add.at(M, (amap[la[m]], amap[lb[m]]), 1)
        pl = np.full(self.next_pid, -1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                pl[pid] = p["lin"]
        rl = np.where(self.cell_pol >= 0, pl[np.maximum(self.cell_pol, 0)],
                      -1)
        m = occ & (rl >= 0) & (rl != self.lin)
        m &= amap[np.maximum(rl, 0)] >= 0
        np.add.at(M, (amap[self.lin[m]], amap[rl[m]]), 0.5)
        M = M + M.T
        for (x, y), t in self.ties.items():
            a, b = pl[x], pl[y]
            if a >= 0 and b >= 0 and a != b and amap[a] >= 0 and amap[b] >= 0:
                M[amap[a], amap[b]] += 30 * t
                M[amap[b], amap[a]] += 30 * t
        C = np.clip(M / 60, 0, 1)
        inn = self.innov[A]

        def diffuse(v, rate):
            gap = np.clip(v[None, :] - v[:, None], 0, None)
            return rate * (C * gap).max(1) * (0.3 + inn)

        g = 0.5 + 0.5 * np.clip(np.log10(1 + Lpop[A]) / 6, 0, 1)
        ag, mt, sl, ad = (self.agri[A], self.metal[A], self.sail[A],
                          self.admin[A])
        nc = ncity[A]
        ag2 = ag + DT * (0.0009 * inn * g * (1 - ag) + diffuse(ag, 0.004))
        mt2 = mt + DT * (0.0005 * inn ** 2 * (ag > 0.5) *
                         (1 + np.log1p(nc) / 3) + diffuse(mt, 0.0008))
        sl2 = sl + DT * (0.0012 * self.seaf[A] * (coastal[A] + 0.1) *
                         (1 - sl) + diffuse(sl, 0.001))
        ad2 = ad + DT * (0.0008 * self.state[A] * (1 - ad) *
                         np.sqrt(np.clip(nc / 5, 0, 1)) + diffuse(ad, 0.002))
        cap = np.where(~self.bronze[A], 1.2,
                       np.where(~self.iron[A], 2.0, 3.5))
        self.agri[A] = np.clip(ag2, 0, 1)
        self.metal[A] = np.minimum(mt2, cap)
        self.sail[A], self.admin[A] = sl2, ad2
        # ore access: own land near ores, or close contact with a holder
        has = {}
        for nm, d in (("cu", W.d_cu), ("sn", W.d_sn), ("fe", W.d_fe)):
            near = occ & (d < 120) & \
                (self.pop * self.peat[np.maximum(self.cul, 0)] > 1000)
            h = (np.bincount(self.lin[near], minlength=nL) > 0)[A]
            has[nm] = h | ((C * h[None, :]).max(1) > 0.4)
        # a stage needs the lineage's own metallurgy plus the ore in hand
        br = self.bronze[A] | ((self.metal[A] >= 1.0) & has["cu"] & has["sn"])
        fe = self.iron[A] | (br & (self.metal[A] >= 1.8) & has["fe"])
        st = self.steel[A] | (fe & (self.metal[A] >= 2.6) & (nc >= 6))
        for arr, new, nm in ((self.bronze, br, "cast bronze"),
                             (self.iron, fe, "work iron"),
                             (self.steel, st, "forge steel")):
            for L in A[new & ~arr[A]]:
                c = self.Lpeople[L]
                self.first((nm, c), "tech", f"{self.keys[c]} {nm} "
                           f"(first: {self.lname(L)})")
            arr[A] = new
        for nm, v, lv in (("adopt farming", self.agri, 0.5),
                          ("adopt open-sea sailing", self.sail, 0.4),
                          ("adopt bureaucracy", self.admin, 0.5)):
            for L in A[v[A] >= lv]:
                c = self.Lpeople[L]
                self.first((nm, c), "tech", f"{self.keys[c]} {nm} "
                           f"(first: {self.lname(L)})")

    # ---- disasters
    def disasters(self):
        W, rng = self.W, self.rng
        self.drought += (1 - self.drought) * 0.35
        if rng.random() < 0.08:
            i = int(rng.integers(W.N))
            rad = rng.uniform(400, 1500)
            sev = rng.uniform(0.35, 0.7)
            d = gc_km(W.xyz, i, np.arange(W.N))
            f = np.clip(1 - d / rad, 0, 1)
            self.drought = np.minimum(self.drought, 1 - sev * f)
            hit = (self.pop * (f > 0.3)).sum()
            if hit > 1e6:
                self.log("drought", f"great drought centred {self.place(i)} "
                         f"({hit/1e6:.1f}M people affected)")
        urban = sum(self.pop[c] for c in self.cities)
        if self.cities and self.tick >= getattr(self, "_plague_next", 0) \
                and rng.random() < 0.04 * min(1, urban / 3e6):
            self._plague_next = self.tick + 10
            cc = np.fromiter(self.cities.keys(), int)
            wt = self.pop[cc]
            o = int(rng.choice(cc, p=wt / wt.sum()))
            start = self.cities[o]["polity"]
            if start not in self.polities:
                return
            hit = {start}
            frontier = [start]
            for _ in range(4):
                nxt = []
                for x in frontier:
                    for k in self.adj:
                        if x in k:
                            y = k[1] if k[0] == x else k[0]
                            if y in hit:
                                continue
                            pr = 0.25 + 0.6 * self.ties.get(k, 0)
                            if rng.random() < pr:
                                hit.add(y)
                                nxt.append(y)
                frontier = nxt
            mort = rng.uniform(0.15, 0.35)
            mask = np.isin(self.cell_pol, list(hit))
            dead = (self.pop * mask).sum() * mort
            self.pop[mask] *= 1 - mort
            for x in hit:
                for c in self.polities[x]["cities"]:
                    self.pop[c] *= 1 - 0.3 * mort
            if dead > 2e5:
                self.log("plague", f"plague from {self.place(o)} through "
                         f"{len(hit)} states, ~{dead/1e6:.2f}M dead")

    # ---- bookkeeping
    def people_summary(self):
        """Per people: population, living lineages, best tech stage, best
        farming level."""
        nP, nL = self.nP, self.nL
        occ = self.lin >= 0
        popc = np.bincount(self.cul[occ], weights=self.pop[occ], minlength=nP)
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        out = []
        for c in range(nP):
            Ls = np.nonzero((self.Lpeople[:nL] == c) & (Lpop > 0))[0]
            stage = ("St" if self.steel[Ls].any() else
                     "Fe" if self.iron[Ls].any() else
                     "Br" if self.bronze[Ls].any() else "")
            out.append(dict(pop=popc[c], nlin=len(Ls), stage=stage,
                            agri=float(self.agri[Ls].max()) if len(Ls) else 0,
                            metal=float(self.metal[Ls].max())
                            if len(Ls) else 0))
        return out

    def record(self):
        nP = self.nP
        occ = self.cul >= 0
        cells = np.bincount(self.cul[occ], minlength=nP)
        ncity = np.zeros(nP, int)
        for r in self.cities.values():
            ncity[r["culture"]] += 1
        live = [p for p in self.polities.values() if p["ended"] is None]
        big = max((p["n_cells"] for p in live), default=0)
        bigkm = max((p.get("km2", 0) for p in live), default=0)
        ps = self.people_summary()
        for c in range(nP):
            if ps[c]["pop"] > 0:
                self.p_seen[c] = True
            elif self.p_seen[c] and not self.p_extinct[c]:
                self.p_extinct[c] = True
                self.log("extinction", f"the last {self.P[c]['label']} are "
                         "gone")
        # population-weighted mean traits, world and per people
        o = np.nonzero(self.lin >= 0)[0]
        w, Lo, co = self.pop[o], self.lin[o], self.cul[o]
        tr = {}
        for t in ("violence", "tolerance", "expansion"):
            v = self.LT[Lo, TI[t]]
            tr[f"{t}_world"] = float((w * v).sum() / max(w.sum(), 1))
            s = np.bincount(co, weights=w * v, minlength=nP)
            n = np.bincount(co, weights=w, minlength=nP)
            for i, k in enumerate(self.keys):
                tr[f"{t}_{k}"] = float(s[i] / n[i]) if n[i] > 0 else None
        self.ts.append(dict(year=self.year, **tr, **{
            f"pop_{k}": float(ps[i]["pop"]) for i, k in enumerate(self.keys)},
            **{f"cells_{k}": int(cells[i]) for i, k in enumerate(self.keys)},
            **{f"cities_{k}": int(ncity[i]) for i, k in enumerate(self.keys)},
            **{f"lineages_{k}": ps[i]["nlin"] for i, k in
               enumerate(self.keys)},
            n_polities=len(live), largest_polity_cells=int(big),
            largest_polity_Mkm2=round(bigkm / 1e6, 3),
            wars=len(self.wars), alliances=len(self.allies),
            multi_people_states=sum(1 for p in live
                                    if len(p["peoples"]) > 1),
            **{f"agri_{k}": ps[i]["agri"] for i, k in enumerate(self.keys)},
            **{f"metal_{k}": ps[i]["metal"] for i, k in
               enumerate(self.keys)}))
        for cell in self.cities:
            hinter = self.pop[self.cell_city == cell].sum()
            size = 0.08 * self.pop[cell] + 0.04 * hinter
            self.city_size[cell] = size
            rec = self.cities[cell]
            rec["peak"] = max(rec["peak"], size)
            self.city_years[cell] += DT
            self.city_peak[cell] = max(self.city_peak[cell], size)

    def step(self):
        self._sim = {}
        self.place_arrivals()
        self.technology()
        self.prepare_capacity()
        self.grow()
        self.migrate()
        self.raids()
        self.tidy()
        self.update_cities()
        self.territory()
        self.polity_stats()
        self.trade_ties()
        self.diplomacy()
        self.wars_step()
        self.rebellions()
        self.disasters()
        self.tidy()
        self.record()
        self.tick += 1
        self.year += DT

    def run(self, verbose=True):
        t0 = time.time()
        nt = self.years // DT
        for _ in range(nt):
            self.step()
            if self.tick % self.frame_every == 0 or self.tick == nt:
                self.frames.append(render(self))
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
def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def borders_mask(lab2):
    b = np.zeros(lab2.shape, bool)
    b[:, :-1] |= lab2[:, :-1] != lab2[:, 1:]
    b[:-1, :] |= lab2[:-1, :] != lab2[1:, :]
    return b


def render(sim, scale=2):
    W = sim.W
    r0, r1 = W.r0, W.r1
    occ = sim.cul >= 0
    dens = np.where(occ, sim.pop / W.area, 0)
    a = np.clip(np.log10(1 + dens) / np.log10(1 + 60), 0.4, 1)

    # political map
    pol = W.base.astype(float).copy()
    pid = sim.cell_pol
    pc = np.zeros((sim.next_pid, 3))
    for k, p in sim.polities.items():
        pc[k] = p["col"]
    m = pid >= 0
    rr, cc = W.row, W.col
    tribal = occ & ~m
    col_t = sim.colors[np.maximum(sim.cul, 0)].astype(float)
    pol[rr[tribal], cc[tribal]] = 0.6 * pol[rr[tribal], cc[tribal]] + \
        0.4 * col_t[tribal]
    pol[rr[m], cc[m]] = 0.15 * pol[rr[m], cc[m]] + 0.85 * pc[pid[m]]
    lab = -np.ones((NY, NX), int)
    lab[rr, cc] = np.where(m, pid, -2)
    lab[~W.land2] = -3
    bm = borders_mask(lab) & W.land2 & (lab >= 0)
    pol[bm] = pol[bm] * 0.25

    # peoples map
    eth = W.base.astype(float).copy()
    eth[rr[occ], cc[occ]] = (1 - a[occ, None]) * eth[rr[occ], cc[occ]] + \
        a[occ, None] * col_t[occ]

    def panel(img):
        im = img[r0:r1].clip(0, 255).astype(np.uint8)
        im = np.repeat(np.repeat(im, scale, 0), scale, 1)
        return Image.fromarray(im)

    P1, P2 = panel(pol), panel(eth)
    for P, dots in ((P1, True), (P2, True)):
        d = ImageDraw.Draw(P)
        for cell, rec in sim.cities.items():
            s = sim.city_size.get(cell, 0)
            rad = 1 + 1.2 * math.log10(1 + s / 2000)
            x = (W.col[cell] + 0.5) * scale
            y = (W.row[cell] - r0 + 0.5) * scale
            p = sim.polities.get(rec["polity"])
            cap = p is not None and p["capital"] == cell
            d.ellipse([x - rad, y - rad, x + rad, y + rad],
                      fill=(255, 255, 255) if cap else (235, 230, 215),
                      outline=(0, 0, 0))
            if cap and p["n_cells"] > 250:
                d.ellipse([x - rad - 3, y - rad - 3, x + rad + 3, y + rad + 3],
                          outline=(255, 255, 255), width=2)
    d = ImageDraw.Draw(P1)
    f = font(13)
    live = sorted([p for p in sim.polities.values() if p["ended"] is None],
                  key=lambda p: -p["n_cells"])[:10]
    for p in live:
        if p["n_cells"] < 150:
            break
        c = p["capital"]
        x = (W.col[c] + 0.5) * scale + 6
        y = (W.row[c] - r0 + 0.5) * scale - 6
        d.text((x, y), sim.pname(p["id"]), fill=(255, 255, 255), font=f,
               stroke_width=2, stroke_fill=(0, 0, 0))

    w, h = P1.size
    rows = (sim.nP + 4) // 5
    hdr = 14 + 38 * rows
    out = Image.new("RGB", (w, 2 * h + hdr + 6), (16, 18, 24))
    out.paste(P1, (0, hdr))
    out.paste(P2, (0, hdr + h + 6))
    d = ImageDraw.Draw(out)
    d.text((12, 8), f"Year {sim.year}", fill=(240, 240, 240), font=font(24))
    ps = sim.people_summary()
    for i, k in enumerate(sim.keys):
        x = 150 + 225 * (i % 5)
        y0 = 38 * (i // 5)
        d.rectangle([x, 12 + y0, x + 14, 26 + y0], fill=tuple(sim.colors[i]))
        d.text((x + 20, 8 + y0), f"{sim.P[i]['label']}",
               fill=(230, 230, 230), font=font(13))
        d.text((x + 20, 26 + y0), f"{ps[i]['pop']/1e6:5.2f}M "
               f"{ps[i]['nlin']} lin {ps[i]['stage']}",
               fill=(170, 170, 170), font=font(12))
    nl = sum(1 for p in sim.polities.values() if p["ended"] is None)
    d.text((12, 40), f"states {nl}", fill=(230, 230, 230), font=font(13))
    d.text((12, 58), f"wars {len(sim.wars)}", fill=(230, 230, 230),
           font=font(13))
    return out


def legacy_map(sim, scale=2):
    """Where cities stood and how far the great states once reached."""
    W = sim.W
    r0, r1 = W.r0, W.r1
    img = W.base.astype(float) * 0.55
    im = Image.fromarray(np.repeat(np.repeat(
        img[r0:r1].astype(np.uint8), scale, 0), scale, 1))
    d = ImageDraw.Draw(im, "RGBA")
    greats = sorted([p for p in sim.polities.values()
                     if p["peak_mask"] is not None],
                    key=lambda p: -p["peak_cells"])[:14]
    f = font(13)
    for p in greats:
        msk = np.zeros((NY, NX), bool)
        msk[W.row[p["peak_mask"]], W.col[p["peak_mask"]]] = True
        edge = msk & ~ndimage.binary_erosion(msk)
        col = tuple(int(v) for v in sim.colors[p["culture"]])
        ys, xs = np.nonzero(msk[r0:r1])
        for y, x in zip(ys, xs):
            d.rectangle([x * scale, y * scale, x * scale + scale - 1,
                         y * scale + scale - 1], fill=col + (38,))
        ys, xs = np.nonzero(edge[r0:r1])
        for y, x in zip(ys, xs):
            d.rectangle([x * scale, y * scale, x * scale + scale - 1,
                         y * scale + scale - 1], fill=col + (230,))
    order = np.argsort(sim.city_years)
    for cell in order[sim.city_years[order] > 0]:
        yrs = sim.city_years[cell]
        rad = 1 + 1.3 * math.log10(1 + sim.city_peak[cell] / 2000)
        al = int(np.clip(70 + yrs / 8, 70, 255))
        x = (W.col[cell] + 0.5) * scale
        y = (W.row[cell] - r0 + 0.5) * scale
        rc = [r for r in sim.city_hist if r["cell"] == cell]
        c = sim.colors[rc[-1]["culture"]] if rc else (255, 255, 255)
        d.ellipse([x - rad, y - rad, x + rad, y + rad],
                  fill=tuple(int(v) for v in c) + (al,),
                  outline=(255, 255, 255, al))
    placed = []
    for p in greats:
        msk_cells = p["peak_mask"]
        cy = (np.median(W.row[msk_cells]) - r0) * scale
        cx = np.median(W.col[msk_cells]) * scale
        if any(abs(cx - x) < 150 and abs(cy - y) < 18 for x, y in placed):
            continue
        placed.append((cx, cy))
        end = p["ended"] if p["ended"] is not None else "now"
        d.text((cx, cy),
               f"{sim.pname(p['id'])} {p['founded']}-{end}",
               fill=(255, 255, 255, 255), font=f, stroke_width=2,
               stroke_fill=(0, 0, 0, 255))
    hdr = Image.new("RGB", (im.size[0], im.size[1] + 40), (16, 18, 24))
    hdr.paste(im, (0, 40))
    dd = ImageDraw.Draw(hdr)
    dd.text((12, 8), f"Legacy after {sim.year} years: cities (size = peak, "
            f"opacity = years inhabited) and the peak extent of the "
            f"{len(greats)} largest states", fill=(235, 235, 235),
            font=font(16))
    return hdr


def population_plot(sim, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = [s["year"] for s in sim.ts]
    fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    ys = [[s[f"pop_{k}"] / 1e6 for s in sim.ts] for k in sim.keys]
    cols = sim.colors / 255
    ax[0].stackplot(yrs, ys, colors=cols,
                    labels=[f"{k} {p['label']}" for k, p in
                            zip(sim.keys, sim.P)])
    ax[0].set_ylabel("population (M)")
    ax[0].legend(loc="upper left", fontsize=8, frameon=False)
    for i, k in enumerate(sim.keys):
        ax[1].plot(yrs, [s[f"cities_{k}"] for s in sim.ts], color=cols[i])
    ax[1].set_ylabel("cities")
    ax[2].plot(yrs, [s["n_polities"] for s in sim.ts], color="k",
               label="states")
    ax2 = ax[2].twinx()
    ax2.plot(yrs, [s["largest_polity_Mkm2"] for s in sim.ts],
             color="tab:red", label="largest state")
    ax[2].set_ylabel("number of states")
    ax2.set_ylabel("largest state (M km2)", color="tab:red")
    ax[2].set_xlabel("year")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def trait_plot(sim, path, traits=("violence", "tolerance")):
    """Population-weighted mean of each trait over time: world (black)
    and per people."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = np.array([s["year"] for s in sim.ts])
    cols = sim.colors / 255
    fig, ax = plt.subplots(len(traits), 1, figsize=(11, 4 * len(traits)),
                           sharex=True)
    for a, t in zip(np.atleast_1d(ax), traits):
        for i, k in enumerate(sim.keys):
            y = np.array([np.nan if s[f"{t}_{k}"] is None else s[f"{t}_{k}"]
                          for s in sim.ts])
            a.plot(yrs, y, color=cols[i], lw=1.2, label=sim.P[i]["label"])
        a.plot(yrs, [s[f"{t}_world"] for s in sim.ts], color="k", lw=2.6,
               label="world")
        a.set_ylabel(f"mean {t}")
        a.set_ylim(0, 1)
        a.spines[["top", "right"]].set_visible(False)
    np.atleast_1d(ax)[0].legend(loc="upper left", fontsize=8, ncol=6,
                                frameon=False)
    np.atleast_1d(ax)[-1].set_xlabel("year")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def lineage_map(sim, scale=2):
    """Final map of living lineages: hue = people, shade = lineage; thin
    lines separate lineages, thick lines separate peoples."""
    W = sim.W
    r0, r1 = W.r0, W.r1
    img = W.base.astype(float).copy()
    occ = sim.lin >= 0
    rr, cc = W.row[occ], W.col[occ]
    img[rr, cc] = 0.2 * img[rr, cc] + 0.8 * sim.Lcol[sim.lin[occ]]
    lab = -np.ones((NY, NX), int)
    lab[W.row, W.col] = sim.lin
    peo = -np.ones((NY, NX), int)
    peo[W.row, W.col] = sim.cul
    bl = borders_mask(lab) & (lab >= 0)
    bp = borders_mask(peo) & (peo >= 0)
    img[bl] *= 0.6
    img[bp] *= 0.15
    im = img[r0:r1].clip(0, 255).astype(np.uint8)
    im = Image.fromarray(np.repeat(np.repeat(im, scale, 0), scale, 1))
    d = ImageDraw.Draw(im)
    occi = np.nonzero(occ)[0]
    Lpop = np.bincount(sim.lin[occi], weights=sim.pop[occi], minlength=sim.nL)
    for L in np.argsort(Lpop)[::-1][:40]:
        if Lpop[L] < 5e5:
            break
        cells = occi[sim.lin[occi] == L]
        y = (np.median(W.row[cells]) - r0) * scale
        x = np.median(W.col[cells]) * scale
        d.text((x, y), sim.lname(L), fill=(255, 255, 255), font=font(12),
               stroke_width=2, stroke_fill=(0, 0, 0))
    out = Image.new("RGB", (im.size[0], im.size[1] + 40), (16, 18, 24))
    out.paste(im, (0, 40))
    ImageDraw.Draw(out).text(
        (12, 8), f"Lineages in year {sim.year} ({int((Lpop > 0).sum())} "
        f"living): hue = people, shade = lineage", fill=(235, 235, 235),
        font=font(16))
    return out


def write_outputs(sim, out):
    os.makedirs(out, exist_ok=True)
    fr = sim.frames
    if fr:
        small = [f.resize((f.size[0] * 3 // 4, f.size[1] * 3 // 4),
                          Image.LANCZOS) for f in fr]
        pal = [f.quantize(colors=200, method=Image.Quantize.MEDIANCUT)
               for f in small]
        pal[0].save(os.path.join(out, "history.gif"), save_all=True,
                    append_images=pal[1:], duration=140, loop=0,
                    optimize=False)
        fr[-1].save(os.path.join(out, "final.png"))
        fdir = os.path.join(out, "frames")
        os.makedirs(fdir, exist_ok=True)
        for k, f in enumerate(fr):
            f.save(os.path.join(fdir, f"f{k:04d}.png"))
    legacy_map(sim).save(os.path.join(out, "legacy.png"))
    lineage_map(sim).save(os.path.join(out, "lineages.png"))
    population_plot(sim, os.path.join(out, "population.png"))
    trait_plot(sim, os.path.join(out, "violence.png"))
    with open(os.path.join(out, "traits.txt"), "w") as fh:
        fh.write(f"seed {sim.seed}, people variation {sim.vary}, start-group "
                 f"variation {sim.start_vary}, lineage drift {sim.drift}\n\n")
        for c, p in enumerate(sim.P):
            fh.write(f"{p['key']} {p['label']}\n  r={p['r']:.4f}  " +
                     "  ".join(f"{t}={p.get(t, 0.5):.2f}" for t in TRAITS) +
                     "\n  affinity " + "  ".join(
                         f"{b}={v:.2f}" for b, v in p["affinity"].items()) +
                     (f"\n  head start {p['head']} yrs" if p.get("head")
                      else "") +
                     f"\n  size {sim.psize[c]:g}  food/head {sim.peat[c]:.2f}"
                     + "\n")
            for L in range(sim.nL):
                if sim.Lpeople[L] == c and sim.Lhow[L] == "start":
                    fh.write(f"    start {sim.lname(L)} r={sim.Lr[L]:.4f}  " +
                             "  ".join(f"{t[:4]}={sim.LT[L, k]:.2f}"
                                       for k, t in enumerate(TRAITS)) + "\n")
            fh.write("\n")
    with open(os.path.join(out, "lineages.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "people", "parent", "how", "founded", "ended",
                    "peak_pop", "stage", "agri", "metal", "sail", "admin",
                    "r"] + TRAITS)
        for L in range(sim.nL):
            stage = ("steel" if sim.steel[L] else "iron" if sim.iron[L] else
                     "bronze" if sim.bronze[L] else "")
            w.writerow([L, sim.keys[sim.Lpeople[L]], sim.Lparent[L],
                        sim.Lhow[L], sim.Lfounded[L],
                        sim.Lended[L] if sim.Lended[L] >= 0 else "",
                        int(sim.Lpeak[L]), stage, round(sim.agri[L], 3),
                        round(sim.metal[L], 3), round(sim.sail[L], 3),
                        round(sim.admin[L], 3), round(sim.Lr[L], 4)] +
                       [round(v, 3) for v in sim.LT[L]])
    with open(os.path.join(out, "events.txt"), "w") as fh:
        for y, k, t in sim.events:
            fh.write(f"{y:5d}  {k:10s} {t}\n")
    import re
    great = {p["id"] for p in sorted(sim.polities.values(),
                                     key=lambda p: -p["peak_cells"])[:15]}
    always = {"origin", "contact", "trade", "tech", "voyage", "city",
              "fusion", "extinction"}
    with open(os.path.join(out, "chronicle.txt"), "w") as fh:
        fh.write("Major events only: world-firsts, great plagues and "
                 "droughts, and events touching the 15 largest states.\n\n")
        for y, k, t in sim.events:
            ids = {int(x) for x in re.findall(r"P(\d+)\(", t)}
            if k in always or (ids & great) or \
                    (k in ("plague", "drought") and "M" in t and
                     float(re.findall(r"([\d.]+)M", t)[0]) >= 2):
                fh.write(f"{y:5d}  {k:10s} {t}\n")
    with open(os.path.join(out, "cities.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "lon", "lat", "people", "founded", "ended",
                    "end_reason", "years", "peak_size", "n_rulers",
                    "rulers"])
        for r in sim.city_hist:
            end = r["ended"] if r["ended"] is not None else sim.year
            w.writerow([r["cell"], f"{r['lon']:.2f}", f"{r['lat']:.2f}",
                        sim.keys[r["culture"]], r["founded"], r["ended"],
                        r["end_reason"], end - r["founded"],
                        int(r["peak"]), len(set(r["owners"])),
                        " ".join(f"P{x}" for x in dict.fromkeys(r["owners"]))])
    with open(os.path.join(out, "polities.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "people", "lineage", "peoples_ruled", "founded",
                    "ended", "years", "parent", "peak_cells", "peak_km2",
                    "peak_year", "peak_cities", "peak_pop", "capital_lon",
                    "capital_lat"])
        for p in sim.polities.values():
            end = p["ended"] if p["ended"] is not None else sim.year
            cap = p["capital"]
            km2 = sim.W.area[p["peak_mask"]].sum() if p["peak_mask"] \
                is not None else ""
            w.writerow([p["id"], sim.keys[p["culture"]], f"L{p['lin']}",
                        " ".join(sim.keys[c] for c in sorted(p["peoples"])),
                        p["founded"],
                        p["ended"], end - p["founded"], p["parent"],
                        p["peak_cells"], km2 and int(km2), p["peak_year"],
                        p["peak_cities"], int(p["peak_pop"]),
                        f"{sim.W.lon[cap]:.2f}", f"{sim.W.lat[cap]:.2f}"])
    with open(os.path.join(out, "timeseries.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sim.ts[0]))
        w.writeheader()
        w.writerows(sim.ts)
    np.savez_compressed(os.path.join(out, "final_state.npz"),
                        row=sim.W.row, col=sim.W.col, pop=sim.pop,
                        people=sim.cul, lineage=sim.lin, polity=sim.cell_pol,
                        city_years=sim.city_years, city_peak=sim.city_peak)
    with open(os.path.join(out, "run.json"), "w") as fh:
        json.dump(dict(seed=sim.seed, years=sim.years, dt=DT,
                       peoples=sim.P, vary=sim.vary, starts=sim.starts,
                       start_vary=sim.start_vary, drift=sim.drift,
                       start_pool=sim.start_pool,
                       cluster_km=sim.cluster_km,
                       settle_drift=sim.settle_drift,
                       size_food=sim.size_food, city_pop=CITY_POP,
                       start_mode=sim.start_mode,
                       wander_steps=sim.wander_steps,
                       city_cap=(CITY_CAP0, CITY_CAP1)), fh, indent=1,
                  default=str)


def main():
    global CITY_POP, CITY_CAP0, CITY_CAP1
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=6000)
    ap.add_argument("--frame-every", type=int, default=20,
                    help="ticks between animation frames")
    ap.add_argument("--homelands", choices=["continents", "anywhere"],
                    default="continents",
                    help="continents: founders start on the two large "
                    "landmasses so peoples meet; anywhere: any good site")
    ap.add_argument("--vary", type=float, default=0.0,
                    help="per-run trait jitter (0 = peoples.py as written; "
                    "0.3 = strong)")
    ap.add_argument("--peoples", default="peoples",
                    help="module in sim/ defining PEOPLES "
                    "(e.g. peoples_fantasy)")
    ap.add_argument("--start-pool", type=float, default=0.02,
                    help="share of habitable cells founders may start in "
                    "(0 = only the best ~60 sites; 0.3 = wide)")
    ap.add_argument("--starts", type=int, default=3,
                    help="founding groups per people (a roster entry's "
                    "'starts' overrides)")
    ap.add_argument("--start-vary", type=float, default=0.05,
                    help="trait jitter between a people's founding groups")
    ap.add_argument("--drift", type=float, default=0.06,
                    help="trait mutation when a daughter lineage splits off")
    ap.add_argument("--cluster-km", type=float, default=0,
                    help="if >0, a people's later groups start within this "
                    "distance of its first; 0 = anywhere")
    ap.add_argument("--settle-drift", type=float, default=0.03,
                    help="trait mutation when a lineage settles a new 5-deg "
                    "region (founds a daughter lineage); 0 = off")
    ap.add_argument("--size-food", choices=["none", "kleiber"],
                    default="kleiber",
                    help="kleiber: each head eats size**0.75 humans' food, "
                    "so large peoples live sparser")
    ap.add_argument("--city-pop", type=float, default=CITY_POP,
                    help="food-equivalent cell population that founds a "
                    "city (a roster `city` factor scales it per people)")
    ap.add_argument("--city-cap", type=float, nargs=2,
                    default=(CITY_CAP0, CITY_CAP1), metavar=("CAP0", "CAP1"),
                    help="city size cap = city-pop * (CAP0 + CAP1 * admin^2)")
    ap.add_argument("--start-mode", choices=["wander", "score"],
                    default="wander",
                    help="wander: founders random-walk toward suitable land "
                    "before the run; score: pick sites by suitability")
    ap.add_argument("--wander-steps", type=int, default=2000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    CITY_POP = a.city_pop
    CITY_CAP0, CITY_CAP1 = a.city_cap
    out = a.out or os.path.join(HERE, "runs", f"seed{a.seed}")
    t0 = time.time()
    world = World()
    print(f"world: {world.N} land cells, loaded in {time.time()-t0:.1f}s")
    sim = Sim(world, seed=a.seed, years=a.years,
              frame_every=a.frame_every, out=out, homelands=a.homelands,
              peoples=vary_peoples(importlib.import_module(
                  a.peoples).PEOPLES, a.seed, a.vary),
              start_pool=a.start_pool, starts=a.starts,
              start_vary=a.start_vary, drift=a.drift,
              cluster_km=a.cluster_km, settle_drift=a.settle_drift,
              size_food=a.size_food, start_mode=a.start_mode,
              wander_steps=a.wander_steps)
    sim.vary = a.vary
    for p in sim.P:
        print(f"  {p['key']} {p['label']:16s} r={p['r']:.4f} " +
              " ".join(f"{t[:4]}={p.get(t, 0.5):.2f}" for t in TRAITS))
    sim.run()
    write_outputs(sim, out)
    print(f"done in {time.time()-t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
